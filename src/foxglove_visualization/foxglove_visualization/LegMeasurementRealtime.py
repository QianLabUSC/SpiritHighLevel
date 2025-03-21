from scipy.spatial.transform import Rotation
import rclpy
from rclpy.node import Node
from trusses_custom_interfaces.msg import SpiritState
from geometry_msgs.msg import Pose
from trusses_custom_interfaces.msg import RobotMeasurements, SpatialMeasurement
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import time

class RealtimeSubscriber(Node):
    def __init__(self):
        super().__init__('measurement_subscriber')
        self.subscription_state = self.create_subscription(
            SpiritState,
            '/spirit/state_low_speed',
            self.SpiritState_callback,
            10)
        self.subscription_state  # prevent unused variable warning
        self.subscription_mocap = self.create_subscription(
            Pose,
            'spirit/mocap',
            self.Pose_callback,
            10)
        self.subscription_mocap  # prevent unused variable warning
        self.subscription_marker = self.create_subscription(
            Pose,
            'spirit/marker_robot',
            self.marker_pose_callback,
            10)
        self.subscription_marker # prevent unused variable warning
        self.realtime_publisher = self.create_publisher(
            RobotMeasurements,
            'raw_measurements',
            10)
        self.realtime_publisher  # prevent unused variable warning
        self.realtime_pene_publisher = self.create_publisher(
            RobotMeasurements,
            'raw_pene_measurements',
            10)
        self.realtime_pene_publisher  # prevent unused variable warning
        self.spatial_measurement_publisher = self.create_publisher(
            SpatialMeasurement,
            'spatial_measurements',
            10)
        self.spatial_measurement_publisher  # prevent unused variable warning

        # initialize hip positions in body frame
        # now suppose the MoCap gives the CoM location & body orientation
        # the following parameters need to be measured precisely
        self.CoM_Hip_B = np.array([[0.228, -0.228, 0.228, -0.228],
                                    [0.07, 0.07, -0.07, -0.07],
                                    [0.0, 0.0, 0.0, 0.0]])
        # robot state
        self.spirit_state = SpiritState()
        # mocap state
        self.R_WB = np.identity(3)
        self.CoM_pos = np.array([0.0, 0.0, 0.0])
        # front left leg and fron right leg index
        self.idx_fl = 0
        self.idx_fr = 2
        # penetration raw data
        self.curr_pene = False
        self.pene_leg_idx = -1
        self.pene_time_fl = 0.0
        self.pene_depth_fl = 0.0
        self.pene_force_fl = 0.0
        self.pene_time_fr = 0.0
        self.pene_depth_fr = 0.0
        self.pene_force_fr = 0.0
        # buffer to calculate the penetration measurement
        # now only consider the front left and front right legs
        self.pene_time_buffer = []
        self.pene_depth_buffer = []
        self.pene_force_buffer = []
        self.stiffness = 0.0
        self.jointVec = np.zeros((3,4))
        self.jointCurrent = np.zeros((3,4))
        # plot configuration
        # self.lastframe_time = time.time()
        # self.plot_refresh_rate = 10
        '''
        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.xlim_low = 0.0
        self.xlim_high = 0.0
        self.ylim_low = 0.0
        self.ylim_high = 0.0
        self.zlim_low = 0.0
        self.zlim_high = 0.0
        '''

    def forwardKinematicsSolver(self, jointVec, legNum):
        L_Upper=0.206
        L_Lower=0.206
        if legNum==0 or legNum==1:
            L_Adjust=0.10098
        else:
            L_Adjust=-0.10098

        theta_ab=jointVec[2]
        theta_hip=jointVec[0]
        theta_knee=jointVec[1]

        #now for 2d plane calculations
        pInter_xPlane = -L_Upper*np.cos(theta_hip) #gets intermediate point p in x direction of the 2d plane
        pInter_zPlane = -L_Upper*np.sin(theta_hip) #gets the intermediate point p in the z direction of the 2d plane

        pToe_xPlane = pInter_xPlane+L_Lower*np.cos(theta_knee-theta_hip) #gets the toe point in the x direction of the 2d plane
        pToe_zPlane = pInter_zPlane-L_Lower*np.sin(theta_knee-theta_hip) #gets the toe point in the z direction of the 2d plane

        #now for the offsets to convert from plane to real world in translation
        L_OffsetY = L_Adjust*np.cos(theta_ab) #gets the offset in the y direction from the robot leg y 0 to the 0 of the plane
        L_OffsetZ = L_Adjust*np.sin(theta_ab) #gets the offset in the z direction from the robot leg z 0 to the 0 of the plane

        #now for the toe positions
        toeX = pToe_xPlane #the x coordinate in the plane is the same as the final leg x
        toeY = L_OffsetY - pToe_zPlane*np.sin(theta_ab)  # gets the toe y position
        toeZ = L_OffsetZ + pToe_zPlane*np.cos(theta_ab) #gets the toe z position

        toeVec = [toeX,toeY,toeZ]
        return toeVec

    def jacobianSolver(self, jointVec, legNum):
        L_Upper=0.206
        L_Lower=0.206
        if legNum==0 or legNum==1:
            L_Adjust=-0.10098
        else:
            L_Adjust=0.10098
        # theta0 = theta_hip
        # theta1 = theta_knee
        # theta2 = theta_ab
        theta0=jointVec[0]
        theta1=jointVec[1]
        theta2=jointVec[2]
        sin0=np.sin(theta0)
        cos0=np.cos(theta0)
        sin1m0=np.sin(theta1-theta0)
        cos1m0=np.cos(theta1-theta0)
        sin2=np.sin(theta2)
        cos2=np.cos(theta2)
        z1=L_Upper*sin0+L_Lower*sin1m0
        dz1_theta0=L_Upper*cos0-L_Lower*cos1m0
        dz1_theta1=L_Lower*cos1m0
        J=np.zeros((3,3),dtype=np.float64)
        J[0,0]=L_Upper*sin0+L_Lower*sin1m0
        J[0,1]=-L_Lower*sin1m0
        J[1,0]=-dz1_theta0*sin2
        J[1,1]=-dz1_theta1*sin2
        J[1,2]=-L_Adjust*sin2-z1*cos2
        J[2,0]=-dz1_theta0*cos2
        J[2,1]=-dz1_theta1*cos2
        J[2,2]=-L_Adjust*cos2+z1*sin2
        return J

    def toeForceSolver(self, jointVec, jointCurrent, legNum):
        J = self.jacobianSolver(jointVec, legNum)
        try:
            JT_inv = np.linalg.inv(np.transpose(J))
        except:
            JT_inv = np.full((3,3),np.nan)
        jointTorque = 0.546*jointCurrent
        jointTorque[1] = 2.0*jointTorque[1]
        toeForce = JT_inv@jointTorque
        return toeForce

    def update_measurement(self):
        #gets the custom mode
        try:
            custom_mode = self.spirit_state.mode[1]
        except Exception as e:
            self.get_logger().error("MODE NOT SET, not ready yet")
            return
        self.pene_time_fl = self.spirit_state.mainboard_t
        self.pene_time_fr = self.spirit_state.mainboard_t
        #gets the ghost behavior mode
        ghost_behav_mode = self.spirit_state.behavior[1]
        #gets forces during walk, i guess we will develop the later
        # spirit_forces = self.spirit_state.joint_residuals
        #gets user inputs
        user_data = self.spirit_state.user_custom
        current_penetrate = user_data[0]
        science_toe_idx = user_data[1]
        pos_penetrate = user_data[2:5]
        force_penetrate = user_data[5:8]
        # spirit_forces = self.spirit_state.joint_residuals
        # first checks what state we are in
        # custom, mode = behavior
        # 1, 50331648
        # 2, 83886080
        # 3, 117440512
        # 4, 150994944
        # first upadate forces calculated from Jacobian
        fl_toe_force = self.toeForceSolver(self.jointVec[:,self.idx_fl], self.jointCurrent[:,self.idx_fl], self.idx_fl)
        fr_toe_force = self.toeForceSolver(self.jointVec[:,self.idx_fr], self.jointCurrent[:,self.idx_fr], self.idx_fr)
        # note that this is in body frame, let's keep it for now for the demo
        self.pene_force_fl = -fl_toe_force[2]
        self.pene_force_fr = -fr_toe_force[2]
        if (custom_mode < 1e8) or (custom_mode > 1.3e8) or (current_penetrate != 1):
            #we are not in crawl mode
            #and we are in the penetrate, for some reason the custom_Mode is very
            #high for penetrate so we check this
            if self.curr_pene:
                # only calculate stiffness while on front right leg
                if self.pene_leg_idx == self.idx_fr:
                    self.stiffness = self.stiffness_calculation()
                    self.spatial_measurement_publish()
            self.pene_leg_idx = -1
            self.curr_pene = False
            self.pene_time_buffer = []
            self.pene_depth_buffer = []
            self.pene_force_buffer = []
            if(ghost_behav_mode  < 3):
                # while not in penetrate mode, if we are in ghost mode, we use Momentum Observer output
                # front left is leg # 0
                self.pene_force_fl = self.spirit_state.joint_residuals[0]
                # front left is leg # 2
                self.pene_force_fr = self.spirit_state.joint_residuals[4]
                # we still dk the depth
                self.pene_depth_fl = float('nan')
                self.pene_depth_fr = float('nan')
        else:
            # otherwise we are in crawl mode
            self.curr_pene = True
            if self.curr_pene and (science_toe_idx != self.pene_leg_idx):
                # only calculate stiffness while on front right leg
                if self.pene_leg_idx == self.idx_fr:
                    self.stiffness = self.stiffness_calculation()
                    self.spatial_measurement_publish()
                    self.pene_time_buffer = []
                    self.pene_depth_buffer = []
                    self.pene_force_buffer = []
            self.pene_leg_idx = int(science_toe_idx)
            # the depth of non penetration leg should be 0
            self.pene_depth_fl = 0.0
            self.pene_depth_fr = 0.0
            if self.pene_leg_idx == self.idx_fl:
                # front left leg is in penetration
                self.pene_depth_fl = -pos_penetrate[2]   # cropped toe z
                self.pene_force_fl = force_penetrate[2]   # cropped toe current z
                # buffer to calculate stiffness later
                self.pene_time_buffer.append(self.pene_time_fl)
                self.pene_depth_buffer.append(self.pene_depth_fl)
                self.pene_force_buffer.append(self.pene_force_fl)
            elif self.pene_leg_idx == self.idx_fr:
                # front right leg is in penetration
                self.pene_depth_fr = -pos_penetrate[2]   # cropped toe z
                self.pene_force_fr = force_penetrate[2]   # cropped toe current z
                # buffer to calculate stiffness later
                self.pene_time_buffer.append(self.pene_time_fr)
                self.pene_depth_buffer.append(self.pene_depth_fr)
                self.pene_force_buffer.append(self.pene_force_fr)

    # if we don't know toe position and have to calculate from joint position
    def update_toePos_W(self):
        # here we use joint positions to get the leg position in body frame
        # and then convert the leg position from body frame to world frame
    	# toe's position in body frame
    	# initialize the toe position in body frame
        Hip_Toe_B = np.zeros((3,4))
        for i in range(4):
            Hip_Toe_B[:,i] = self.forwardKinematicsSolver(self.jointVec[:,i], i)
        # we want the hip and toe positions in world frame
        # expand CoMPos to a 3x4 array
        self.Hip_W = np.tile(self.CoM_pos[:, np.newaxis], (1, 4)) + self.R_WB @ self.CoM_Hip_B
        self.Toe_W = self.Hip_W + self.R_WB @ Hip_Toe_B
        # determine if we need to update plot
        # if time.time() - self.lastframe_time > 1.0 / self.plot_refresh_rate:
        #     self.plot_4toes()

    def stiffness_calculation(self):
        depth = np.array(self.pene_depth_buffer)
        force = np.array(self.pene_force_buffer)
        maxforce = np.max(force)
        # force that we recognize as start penetration
        # if the maxforce is small, we select the force threshold as 0.90*maxforce, this ensures we get data even if max penetration force is below 10
        force_threshold = min(10.0, 0.90*maxforce)
        # we start searching from the zero height
        # sometimes the depth always greater than 0.0, so we select -0.02
        # the function argmax will give index 0 if cannot find even one satisfying the condition
        depth_zero_idx = 0 #np.argmax(depth > -0.02)
        start_pene_idx = depth_zero_idx
        for i in range(depth_zero_idx, len(depth)):
            if force[i] > force_threshold:
                start_pene_idx = i
                break
        # Perform linear fit
        """
        WE MAY HAVE AN ISSUE WITH POLYFIT GOING TO END OF DATA. THIS IS BECAUSE
        WE HAVE A CLUMPING OF DATA AT THE END. WILL CAUSE SKEWING. FOR NOW LETS 
        DO START_PENE_IDX TO INDEX OF 0.95 OF MAX FORCE 
        
        """
        #FIND END PENE IDX
        max_force_threshold = 0.9*maxforce
        for i in range(depth_zero_idx,len(depth)):
            if force[i] < max_force_threshold:
                end_pene_idx = i
        coefficients = np.polyfit(depth[start_pene_idx:end_pene_idx], force[start_pene_idx:end_pene_idx], 1)
        slope, intercept = coefficients
        return slope

    def SpiritState_callback(self, msg):
        self.spirit_state = msg
        # self.get_logger().info("_".join([str(m) for m in self.spirit_state.mode]))
        # update self.jointVec
        jointPos = self.spirit_state.joint_position
        if len(jointPos)==12:
            # jointPos = [0hip, 0knee, 1hip, 1knee, 2hip, 2knee, 3hip, 3knee, 4hip, 4knee, 0ab, 1ab, 2ab, 3ab]
            # now the jointPos is a 1x12 list, let's make it into a np 3x4 array
            jointPos = np.array([[jointPos[0],jointPos[2],jointPos[4],jointPos[6]],
                                    [jointPos[1],jointPos[3],jointPos[5],jointPos[7]],
                                    [jointPos[8],jointPos[9],jointPos[10],jointPos[11]]])
            # joint position offset
            jointPos[0] = jointPos[0] + 0.1807
            jointPos[1] = jointPos[1] + 0.2325
            self.jointVec = jointPos
        else:
            print("Joint Pos recv error")
        # debug for jointPos
        # print(jointPos)
        # update self.jointCurrent
        jointCurr = self.spirit_state.joint_currents
        if len(jointCurr)==12:
            # jointCurr = [0hip, 0knee, 1hip, 1knee, 2hip, 2knee, 3hip, 3knee, 4hip, 4knee, 0ab, 1ab, 2ab, 3ab]
            # now the jointCurr is a 1x12 list, let's make it into a np 3x4 array
            jointCurr = np.array([[jointCurr[0],jointCurr[2],jointCurr[4],jointCurr[6]],
                                    [jointCurr[1],jointCurr[3],jointCurr[5],jointCurr[7]],
                                    [jointCurr[8],jointCurr[9],jointCurr[10],jointCurr[11]]])
            self.jointCurrent = jointCurr
        else:
            print("Joint Curr recv error")
        # update toe position
        self.update_toePos_W()
        self.update_measurement()
        self.realtime_measurement_publish()

    def Pose_callback(self, msg):
        # Get data from mocap
        mocap_q = np.array([msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w])
        p_WMo_W = np.array([msg.position.x, msg.position.y, msg.position.z])
        
        
        # Init Rotations
        # quaternion to rotation matrix, this is rotation matrix from MoCap to World
        R_WM = Rotation.from_quat(mocap_q).as_matrix()
        R_MB = np.array([[0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0],
                        [1.0, 0.0, 0.0]])
        R_WB = R_WM @ R_MB

        p_BM_B = np.array([0.037,0,0.1075]) #body to tracker in body
        p_WB_W = p_WMo_W + R_WB @ ( -p_BM_B )
        
        self.R_WB = R_WB
        # self.CoM_pos = np.array([msg.position.x, msg.position.y, msg.position.z]) + p_offset
        self.CoM_pos = p_WB_W

        # update toe position
        # self.update_toePos_W()

    def marker_pose_callback(self, msg):
        # Get data from mocap
        self.get_logger().info("Pose Update *******************************")
        mocap_q = np.array([msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w])
        p_WMo_W = np.array([msg.position.x, msg.position.y, msg.position.z])
        
        
        # Init Rotations
        # quaternion to rotation matrix, this is rotation matrix from MoCap to World
        R_WM = Rotation.from_quat(mocap_q).as_matrix()
        R_MB = np.array([[1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0]])
        R_WB = R_WM @ R_MB

        p_BM_B = np.array([0.0,0,0.0]) #body to tracker in body
        p_WB_W = p_WMo_W + R_WB @ ( -p_BM_B )
        
        self.R_WB = R_WB
        # self.CoM_pos = np.array([msg.position.x, msg.position.y, msg.position.z]) + p_offset
        self.CoM_pos = p_WB_W

        self.get_logger().info(np.array2string(self.R_WB))
        self.get_logger().info(np.array2string(self.CoM_pos))

        # update toe position
        # self.update_toePos_W()

    def realtime_measurement_publish(self):
        msg = RobotMeasurements()
        msg.front_left_leg.position.x = self.Toe_W[0,self.idx_fl]
        msg.front_left_leg.position.y = self.Toe_W[1,self.idx_fl]
        msg.front_left_leg.position.z = self.Toe_W[2,self.idx_fl]
        msg.front_left_leg.curr_pene = (self.pene_leg_idx == self.idx_fl)
        msg.front_left_leg.pene_time = self.pene_time_fl
        msg.front_left_leg.pene_depth = self.pene_depth_fl
        msg.front_left_leg.pene_force = self.pene_force_fl
        msg.front_right_leg.position.x = self.Toe_W[0,self.idx_fr]
        msg.front_right_leg.position.y = self.Toe_W[1,self.idx_fr]
        msg.front_right_leg.position.z = self.Toe_W[2,self.idx_fr]
        msg.front_right_leg.curr_pene = (self.pene_leg_idx == self.idx_fr)
        msg.front_right_leg.pene_time = self.pene_time_fr
        msg.front_right_leg.pene_depth = self.pene_depth_fr
        msg.front_right_leg.pene_force = self.pene_force_fr
        self.realtime_publisher.publish(msg)
        # while when either of the leg is in penetration
        # remove pene_depth and pene_force data if not in penetration
        if not msg.front_left_leg.curr_pene:
            msg.front_left_leg.pene_depth = float('nan')
            msg.front_left_leg.pene_force = float('nan')
        if not msg.front_right_leg.curr_pene:
            msg.front_right_leg.pene_depth = float('nan')
            msg.front_right_leg.pene_force = float('nan')
        if msg.front_left_leg.curr_pene or msg.front_right_leg.curr_pene:
            self.realtime_pene_publisher.publish(msg)

    def spatial_measurement_publish(self):
        msg = SpatialMeasurement()
        if (self.pene_leg_idx == self.idx_fr):

            transform_to_map_T_MW = np.array(
                [[-1, 0, 0, 0],
                 [ 0,-1, 0, 2.4],
                 [ 0, 0, 1, 0],
                 [ 0, 0, 0, 1]]
            )
            p_WT_homo = np.zeros((4,1))
            p_WT_homo[0:3,0] = self.Toe_W[:,self.pene_leg_idx]
            p_WT_homo[3,0]   = 1
            p_MT_homo = transform_to_map_T_MW @ p_WT_homo

            msg.position.x = p_MT_homo[0,0]
            msg.position.y = p_MT_homo[1,0]
            msg.position.z = p_MT_homo[2,0]

        msg.uncertainty = 0.0
        msg.leg_idx = self.pene_leg_idx
        msg.value = self.stiffness
        msg.unit = "N/m"
        msg.source_name = "Stiffness"
        msg.time = self.get_clock().now().to_msg()
        # print(self.pene_leg_idx)
        # print(msg)
        self.spatial_measurement_publisher.publish(msg)

    '''
    def plot_4toes(self):
        # use the toe position to plot and update the frame every time called
        self.ax.clear()
        self.ax.scatter(self.Toe_W[0,:], self.Toe_W[1,:], self.Toe_W[2,:])
        # Adjust the limit accordingly
        self.xlim_low = np.min([self.xlim_low, np.min(self.Toe_W[0,:])-1.0])
        self.xlim_high = np.max([self.xlim_high, np.max(self.Toe_W[0,:])+1.0])
        self.ylim_low = np.min([self.ylim_low, np.min(self.Toe_W[1,:])-1.0])
        self.ylim_high = np.max([self.ylim_high, np.max(self.Toe_W[1,:])+1.0])
        self.zlim_low = np.min([self.zlim_low, np.min(self.Toe_W[2,:])-1.0])
        self.zlim_high = np.max([self.zlim_high, np.max(self.Toe_W[2,:])+1.0])
        self.ax.set_xlim(self.xlim_low, self.xlim_high)
        self.ax.set_ylim(self.ylim_low, self.ylim_high)
        self.ax.set_zlim(self.zlim_low, self.zlim_high)
        self.ax.set_xlabel('X axis')
        self.ax.set_ylabel('Y axis')
        self.ax.set_zlabel('Z axis')
        # self.ax.set_aspect('equal')
        plt.draw()
        plt.pause(1.0 / self.plot_refresh_rate)
'''

def main(args=None):
    rclpy.init(args=args)

    realtime_subscriber = RealtimeSubscriber()

    rclpy.spin(realtime_subscriber)

    realtime_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

