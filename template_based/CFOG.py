import cv2
import numpy as np
import math
from common.image_process import SSD_template_matching,filter_outliers,findHomoraphy

def keypoint_obtain(img,num_points,harris_thresh):
    """
    将一副图像分割为625个区域(每行每列都分为25份)，然后使用harris算法在每个小区域中查找关键点
    """
    img=img.astype(np.float32)
    harris_detector=cv2.cornerHarris(img,2,3,0.04)
    num_split=int(math.sqrt(num_points))
    x_unit_len=int(img.shape[0]/num_split)
    y_unit_len=int(img.shape[1]/num_split)
    key_point=[]
    for index_i in range(num_split):
        for index_j in range(num_split):
            harris_index=harris_detector[index_i*x_unit_len:index_i*x_unit_len+x_unit_len,
                                         index_j*y_unit_len:index_j*y_unit_len+y_unit_len]#harris的值有正有负，分别表示不同的变化，绝对值越大，变化越明显
            harris_index=abs(harris_index)
            #找到其中的最大值的位置；如果最大值不大于阈值，则跳过；否则，记录下该点在原图实际位置
            min_v,max_v,min_loc,max_loc = cv2.minMaxLoc(harris_index)
            if max_v>harris_thresh:
                max_loc=np.array([max_loc[1],max_loc[0]])
                max_loc=max_loc+np.array([index_i*x_unit_len,index_j*y_unit_len])
                key_point.append((max_loc[0],max_loc[1]))
            else:
                continue
    return key_point

def one_keypoint_matching(keypoint,fea_ref,fea_sen,attention,window_size=100,search_rad=60):
    x_ref=keypoint[0]
    y_ref=keypoint[1]
    half_window_size=int(window_size/2)
    fea_ref_temp=fea_ref[x_ref-half_window_size:x_ref+half_window_size,
                            y_ref-half_window_size:y_ref+half_window_size].astype(np.float32)
    if attention is not None:
        attention_temp=attention[x_ref-half_window_size:x_ref+half_window_size,
                            y_ref-half_window_size:y_ref+half_window_size].astype(np.float32)
    else:
        attention_temp=None
    fea_sen_img = fea_sen[x_ref-half_window_size-search_rad:
                          x_ref+half_window_size+search_rad,
                          y_ref-half_window_size-search_rad:
                          y_ref+half_window_size+search_rad].astype(np.float32)

    m_r=SSD_template_matching(template=fea_ref_temp,
                              image=fea_sen_img,
                              attention=attention_temp,
                              return_score_flag=False)

    _=cv2.minMaxLoc(m_r)
    min_loc=_[2][1],_[2][0]
    cores=x_ref-search_rad+min_loc[0],y_ref-search_rad+min_loc[1]
    return cores

def cfog_matching_points(ref_img,ref_fea,sen_fea,attention,window_size,search_rad,num_points):
    """
    ref_img:用于查找keypoint
    """
    marg = int(window_size / 2 + search_rad)
    k_search = [marg, ref_img.shape[0] - marg, marg, ref_img.shape[1] - marg]
    keypoint_list = keypoint_obtain(ref_img[k_search[0]:k_search[1], k_search[2]:k_search[3]],
                                    num_points=num_points, harris_thresh=50)

    keypoint_list = [(_[0] + marg, _[1] + marg) for _ in keypoint_list]
    sen_point_list = []
    corres_points={}
    for keypoint in keypoint_list:
        sen_point = one_keypoint_matching(keypoint=keypoint,
                                          fea_ref=ref_fea,
                                          fea_sen=sen_fea,
                                          attention=attention,
                                          window_size=window_size,
                                          search_rad=search_rad)
        sen_point_list.append(sen_point)
        corres_points.update({tuple(keypoint):[tuple(sen_point),0]})
    return corres_points



class CFOG_descriptor():
    def __init__(self, img,  bin_size):
        self.img = img
        self.bin_size = bin_size
        self.angle_unit = 2*np.pi / self.bin_size  # 0~360度，bin_size（9）个方向的偏导

    def global_gradient(self):
        #得到每个像素的梯度
        gradient_values_x = cv2.Sobel(self.img, cv2.CV_64F, 1, 0, ksize=5)#水平
        gradient_values_y = cv2.Sobel(self.img, cv2.CV_64F, 0, 1, ksize=5)#垂直
        # gradient_magnitude = np.sqrt(gradient_values_x**2 + gradient_values_y**2)#总的大小
        # gradient_angle = cv2.phase(gradient_values_x, gradient_values_y, angleInDegrees=True)#方向
        return gradient_values_x, gradient_values_y

    def cell_gradient(self, cell_gradient_x, cell_gradient_y):
        #得到cell的梯度直方图
        orientation_centers = [0] * self.bin_size
        for index in range(self.bin_size):
            angle=(self.angle_unit)*index
            orientation_centers[index]=abs(cell_gradient_x*math.cos(angle)+cell_gradient_y*math.sin(angle)) #这里的abs解决了明暗相反的问题

        return orientation_centers

    def feature_show(self, feature):
        feature_image=[]
        for index in range(feature.shape[2]):  # 长*宽*方向导  shape[2]是方向导的个个数，共9个方向
            sub_fea=feature[:, :, index]
            # 将 sub_fea 的值标准化到 0 到 255 的范围，并将其转换为 8 位无符号整数类型。
            sub_fea=cv2.normalize(sub_fea,dst=None,alpha=0,beta=255,norm_type=cv2.NORM_MINMAX).astype(np.uint8)
            feature_image.append(sub_fea)
        return feature_image

    def extract(self):
        """
        论文4.1.1
        """
        height, width = self.img.shape #输入影像的大小为[400,400]
        #1.计算每个像素的梯度和方向
        gradient_values_x, gradient_values_y = self.global_gradient() #利用sobel算子计算梯度，然后得到梯度的大小和梯度的方向；其中mag和angle的shape均为[400,400]
        cell_gradient_vector = np.zeros((height , width , self.bin_size)).astype(np.float32) #一个cell是8*8大小，bin是9，所以cell_gradient_vector的大小为[50,50,9]
        for i in range(cell_gradient_vector.shape[0]):
            for j in range(cell_gradient_vector.shape[1]):
                cell_gradient_vector[i][j]=self.cell_gradient(gradient_values_x[i,j],gradient_values_y[i,j])

        #做3D卷积
        cell_gradient_vector_2D=cv2.GaussianBlur(cell_gradient_vector, ksize=(5, 5), sigmaX=0, sigmaY=0)
        cell_gradient_vector_3D=cell_gradient_vector_2D.copy()
        for index in range(cell_gradient_vector_2D.shape[2]):
            cell_gradient_vector_3D[:,:,index]=0.25*cell_gradient_vector_2D[:,:,index-1]+0.25*cell_gradient_vector_2D[:,:,(index+1)%9]+0.5*cell_gradient_vector_2D[:,:,index]
        #归一化向量
        fea_img = self.feature_show(cell_gradient_vector_3D.copy())
        # 计算 cell_gradient_vector_3D 在 axis=2 维度上的向量范数。axis=2 意味着将沿第三个轴（方向导）计算每个向量的模。
        # 增加一个极小值 1e−20 来防止出现零值。
        fea_mag=np.linalg.norm(cell_gradient_vector_3D,axis=2)+1e-20
        # 对每个向量进行归一化，使得每个向量的模为 1。
        cell_gradient_vector_3D=cell_gradient_vector_3D/(fea_mag[:,:,np.newaxis])
        fea_img_norm = self.feature_show(cell_gradient_vector_3D.copy())
        return cell_gradient_vector_3D,fea_mag,fea_img,fea_img_norm

def CFOG_registration(thermal_visible_c,cfg):

        #提取CFOG特征
        thermal_visible_c.get_img_features(method=cfg['fea'],bin_size=cfg['bin_size'])
        #CFOG TAMM配准
        corres=thermal_visible_c.get_correspoints(method='CFOG',
                                                  patch_size=cfg['patch_size'],
                                                  search_radius=cfg['search_radius'],
                                                  num_points=cfg['num_points'])
        thermal_visible_dict=corres
        thermal_list=[]
        visible_list=[]
        for _ in thermal_visible_dict:
            thermal_list.append(_)
            visible_list.append(thermal_visible_dict[_][0])
        #filer points
        thermal_point_list, sen_point_list, outliers_ref, outliers_sen = filter_outliers(thermal_list, visible_list, thresh=cfg['thresh'],method='NBCS')
        good = [[_thermal[1], _thermal[0], _sen[1], _sen[0]] for (_thermal, _sen) in zip(thermal_point_list, sen_point_list)]
        H_mat, flag_result= findHomoraphy(good)
        return H_mat,(thermal_point_list, sen_point_list, outliers_ref, outliers_sen)


