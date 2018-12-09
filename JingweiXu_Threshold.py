class JingweiXu():
    Video_path = '/data/RAIDataset/Video/2.mp4'
    GroundTruth_path = '/data/RAIDataset/Video/gt_2.txt'

    def get_vector(self, segments):
        import sys
        import os
        sys.path.insert(0, '/data/caffe/python')
        import caffe
        import cv2
        import numpy as np
        import math
        import csv

        caffe.set_mode_gpu()
        caffe.set_device(0)
        # load model(.prototxt) and weight (.caffemodel)

        # os.chdir('/data/Meisa/ResNet/ResNet-50')
        # ResNet_Weight = './resnet50_cvgj_iter_320000.caffemodel'  # pretrained on il 2012 and place 205

        os.chdir('/data/Meisa/hybridCNN')
        Hybrid_Weight = './hybridCNN_iter_700000.caffemodel'



        # ResNet_Def = 'deploynew_globalpool.prototxt'

        Hybrid_Def = 'Shot_hybridCNN_deploy_new.prototxt'

        Alexnet_Def = '/data/alexnet/deploy_alexnet_places365.prototxt.txt'
        Alexnet_Weight = '/data/alexnet/alexnet_places365.caffemodel'
        net = caffe.Net(Hybrid_Def,
                        Hybrid_Weight,
                        caffe.TEST)

        # load video
        i_Video = cv2.VideoCapture(self.Video_path)

        # get width of this video
        wid = int(i_Video.get(3))

        # get height of this video
        hei = int(i_Video.get(4))

        # get the number of frames of this video
        framenum = int(i_Video.get(7))

        if i_Video.isOpened():
            success = True
        else:
            success = False
            print('Can\' open this video!')




        transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})

        transformer.set_transpose('data', (2, 0, 1))
        # transformer.set_mean('data', mu)
        transformer.set_raw_scale('data', 255)
        transformer.set_channel_swap('data', (2, 1, 0))

        net.blobs['data'].reshape(1,
                                  3,
                                  227, 227)

        FrameV = []

        if len(segments) == 1:
            i_Video.set(1, segments[0])
            ret, frame = i_Video.read()
            if frame is None:
                print i
            transformed_image = transformer.preprocess('data', frame)
            net.blobs['data'].data[...] = transformed_image
            output = net.forward()
            FrameV.extend(output['fc8'][0].tolist())
            #FrameV.extend(np.squeeze(output['global_pool'][0]).tolist())
            return FrameV

        for i in range(segments[0], segments[1]+1):
            i_Video.set(1, i)
            ret, frame = i_Video.read()
            if frame is None:
                print i
                continue
            transformed_image = transformer.preprocess('data', frame)
            net.blobs['data'].data[...] = transformed_image
            output = net.forward()
            FrameV.append(output['fc8'][0].tolist())
            # FrameV.append(np.squeeze(output['global_pool'][0]).tolist())

        return FrameV




    def RGBToGray(self, RGBImage):

        import numpy as np
        return np.dot(RGBImage[..., :3], [0.299, 0.587, 0.114])


    # Get the Manhattan Distance
    def Manhattan(self, vector1, vector2):
        import numpy as np
        return np.sum(np.abs(vector1 - vector2))


    def getHist(self, frame1, frame2, allpixels):
        binsnumber = 64
        import cv2
        Bframe1hist = cv2.calcHist([frame1], channels=[0], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])
        Bframe2hist = cv2.calcHist([frame2], channels=[0], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])

        Gframe1hist = cv2.calcHist([frame1], channels=[1], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])
        Gframe2hist = cv2.calcHist([frame2], channels=[1], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])

        Rframe1hist = cv2.calcHist([frame1], channels=[2], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])
        Rframe2hist = cv2.calcHist([frame2], channels=[2], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])

        distance = self.Manhattan(Bframe1hist, Bframe2hist) + self.Manhattan(Gframe1hist, Gframe2hist) + self.Manhattan(Rframe1hist, Rframe2hist)
        return distance/(allpixels)

    def getHist_chi_square(self, frame1, frame2, allpixels):

        import cv2

        binsnumber = 64

        Bframe1hist = cv2.calcHist([frame1], channels=[0], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])
        Bframe2hist = cv2.calcHist([frame2], channels=[0], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])

        Gframe1hist = cv2.calcHist([frame1], channels=[1], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])
        Gframe2hist = cv2.calcHist([frame2], channels=[1], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])

        Rframe1hist = cv2.calcHist([frame1], channels=[2], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])
        Rframe2hist = cv2.calcHist([frame2], channels=[2], mask=None, ranges=[0.0,255.0], histSize=[binsnumber])

        distance = cv2.compareHist(Bframe1hist, Bframe2hist, method=cv2.HISTCMP_CHISQR)+cv2.compareHist(Gframe1hist, Gframe2hist, method=cv2.HISTCMP_CHISQR)+cv2.compareHist(Rframe1hist, Rframe2hist, method=cv2.HISTCMP_CHISQR)
        return distance/(allpixels)

    def getPixelDifference(self,frame1, frame2, allpixels):
        import numpy as np
        return np.sum(np.abs(frame1-frame2))/allpixels

    def CutVideoIntoSegments(self):
        import math
        import cv2
        import numpy as np

        # It save the pixel intensity between 20n and 20(n+1)
        d = []
        SegmentsLength = 11
        i_Video = cv2.VideoCapture(self.Video_path)

        # get width of this video
        wid = int(i_Video.get(3))

        # get height of this video
        hei = int(i_Video.get(4))

        if i_Video.isOpened():
            success = True
        else:
            success = False
            print('Can\' open this video!')

        # It save the number of frames in this video
        FrameNumber = int(i_Video.get(7))

        # The number of segments
        Count = int(math.ceil(float(FrameNumber) / float(SegmentsLength)))
        for i in range(Count):

            i_Video.set(1, (SegmentsLength-1)*i)
            ret1, frame_20i = i_Video.read()

            if((SegmentsLength-1)*(i+1)) >= FrameNumber:
                i_Video.set(1, FrameNumber-1)
                ret2, frame_20i1 = i_Video.read()
                # d.append(np.sum(np.abs(self.RGBToGray(frame_20i) - self.RGBToGray(frame_20i1))))

                d.append(self.getHist(frame_20i, frame_20i1, wid*hei))
                break

            i_Video.set(1, (SegmentsLength-1)*(i+1))
            ret2, frame_20i1 = i_Video.read()

            # d.append(np.sum(np.abs(self.RGBToGray(frame_20i) - self.RGBToGray(frame_20i1))))
            d.append(self.getHist(frame_20i, frame_20i1, wid*hei))


        # The number of group
        GroupNumber = int(math.ceil(float(FrameNumber) / 10.0))

        MIUG = np.mean(d)
        a = 0.7 # The range of a is 0.5~0.7
        Tl = [] # It save the Tl of each group
        CandidateSegment = []
        for i in range(GroupNumber):
            MIUL = np.mean(d[10*i:10*i+10])
            SigmaL = np.std(d[10*i:10*i+10])

            Tl.append(MIUL + a*(1+math.log(MIUG/MIUL))*SigmaL)
            for j in range(10):
                if i*10 + j >= len(d):
                    break
                if d[i*10+j]>Tl[i]:
                    CandidateSegment.append([(i*10+j)*(SegmentsLength-1), (i*10+j+1)*(SegmentsLength-1)])
                    #print 'A candidate segment is', (i*10+j)*20, '~', (i*10+j+1)*20

        return CandidateSegment
        #print 'a'



    # Calculate the cosin distance between vector1 and vector2
    def cosin_distance(self, vector1, vector2):
        dot_product = 0.0
        normA = 0.0
        normB = 0.0
        for a, b in zip(vector1, vector2):
            dot_product += a * b
            normA += a ** 2
            normB += b ** 2
        if normA == 0.0 or normB == 0.0:
            return None
        else:
            return dot_product / ((normA * normB) ** 0.5)

    # Calculate the D1
    def getD1(self, Segment):
        return self.cosin_distance(Segment[0], Segment[-1])


####################################The Following is used for evaluating################################################
    def if_overlap(self, begin1, end1, begin2, end2):
        if begin1 > begin2:
            begin1, end1, begin2, end2 = begin2, end2, begin1, end1

        return end1 >= begin2


    def get_union_cnt(self,set1, set2):
        cnt = 0
        for begin, end in set1:
            for _begin, _end in set2:
                if self.if_overlap(begin, end, _begin, _end):
                    cnt += 1
                    break
        return cnt

    def recall_pre_f1(self,a, b, c):
        a = float(a)
        b = float(b)
        c = float(c)
        recall = a / b if b != 0 else 0
        precison = a / c if c != 0 else 0
        f1 = 2 * recall * precison / (recall + precison)
        return precison, recall, f1

    def eval(self, predict, gt):


        gt_cuts = [(begin,end) for begin,end in gt if end-begin==1]
        gt_graduals = [(begin, end) for begin, end in gt if end - begin > 1]

        predicts_cut = [(begin,end) for begin,end in predict if end-begin==1]
        predicts_gradual = [(begin, end) for begin, end in predict if end - begin > 1]

        cut_correct = self.get_union_cnt(gt_cuts, predicts_cut)
        gradual_correct = self.get_union_cnt(gt_graduals, predicts_gradual)
        all_correct = self.get_union_cnt(predicts_cut + predicts_gradual, gt)

        return [cut_correct, gradual_correct, all_correct]

    ##################################################################################



    # Check the segments selected (by the function called CutVideoIntoSegments) whether have cut
    def CheckSegments(self, CandidateSegments):

        import numpy as np

        # It save the cut missed
        MissCutTruth = []
        # It save the gradual missed
        MissGra = []

        with open(self.GroundTruth_path, 'r') as f:
            GroundTruth = f.readlines()

        GroundTruth = [[int(i.strip().split('\t')[0]),int(i.strip().split('\t')[1])] for i in GroundTruth]

        TransitionNumber = len(GroundTruth)

        # It save the Hardcut Truth
        HardCutTruth = []

        # It save the Gradual Truth
        GradualTruth  = []

        GradualTransitionNumber = 0
        HardTruthNumber = 0
        for i in range(0, len(GroundTruth)-1):
            if np.abs(GroundTruth[i][1] - GroundTruth[i+1][0]) != 1:
                GradualTruth.append([GroundTruth[i][1], GroundTruth[i+1][0]])
                GradualTransitionNumber += 1
            else:
                HardCutTruth.append([GroundTruth[i][1], GroundTruth[i+1][0]])
                HardTruthNumber +=1

            for j in range(len(CandidateSegments)):
                if self.if_overlap(CandidateSegments[j][0], CandidateSegments[j][1], GroundTruth[i][1], GroundTruth[i+1][0]):
                    break
                if self.if_overlap(CandidateSegments[j][0], CandidateSegments[j][1], GroundTruth[i][1], GroundTruth[i+1][0]) is False and GroundTruth[i+1][0] < CandidateSegments[j][0]:
                    if np.abs(GroundTruth[i][1] - GroundTruth[i+1][0]) != 1:
                        MissGra.append([GroundTruth[i][1],GroundTruth[i+1][0]])
                    else:
                        MissCutTruth.append([GroundTruth[i][1],GroundTruth[i+1][0]])
                    break

        print 'Hard Rate is ', (HardTruthNumber - len(MissCutTruth))/float(HardTruthNumber)
        print 'Gra Rate is ', (GradualTransitionNumber - len(MissGra))/float(GradualTransitionNumber)
                # if GroundTruth[i][1] >= CandidateSegments[j][0] and GroundTruth[i+1][0] <= CandidateSegments[j][1]:
                #     break
                # elif GroundTruth[i][1] < CandidateSegments[j][0]:
                #     if np.abs(GroundTruth[i][1] - GroundTruth[i + 1][0]) != 1:
                #         MissGra.append([GroundTruth[i][1],GroundTruth[i+1][0]])
                #     else:
                #         MissCutTruth.append([GroundTruth[i][1],GroundTruth[i+1][0]])

                    # print 'This cut "', GroundTruth[i][1],',', GroundTruth[i+1][0],'"can not be detected'
                    # break

        return [HardCutTruth, GradualTruth]
########################Hist Based Method#######################################
    def Mnw(self, n, w):
        import cv2
        i_Video = cv2.VideoCapture(self.Video_path)
        # if n+w == int(n+w):
        #     if int(n+w) >= len(self.Frame) or int(n-w) >= len(self.Frame):
        #         return -1
        #     return self.difference(self.Frame[int(n-w)], self.Frame[int(n+w)])
        # else:
        #     return (1. / 2.) * (self.Mnw(n - 0.5, w) + self.Mnw(n + 0.5, w))
        # get width of this video
        wid = int(i_Video.get(3))

        # get height of this video
        hei = int(i_Video.get(4))

        if n+w == int(n+w):
            i_Video.set(1, n-w)
            ret1, frame1 = i_Video.read()

            i_Video.set(1, n+w)
            ret2, frame2 = i_Video.read()
            return 0.5 * self.getHist_chi_square(frame1, frame2, wid*hei) + 0.5 * self.getHist(frame1, frame2, wid*hei)
        else:
            return (1. / 2.) * (self.Mnw(n - 0.5, w) + self.Mnw(n + 0.5, w))



    def CTDetectionBaseOnHist(self):
        import numpy as np
        import cv2

        k = 0.4
        Tc = 0.05

        CandidateSegments = self.CutVideoIntoSegments()
        # for i in range(len(CandidateSegments)):
        #     FrameV = self.get_vector(CandidateSegments[i])
        [HardCutTruth, GradualTruth] = self.CheckSegments(CandidateSegments)

        # It save the predicted shot boundaries
        Answer = []

        # It save the candidate segments which may have gradual
        CandidateGra = []

        i_Video = cv2.VideoCapture(self.Video_path)

        # get width of this video
        wid = int(i_Video.get(3))

        # get height of this video
        hei = int(i_Video.get(4))
        AnswerLength = 0
        for i in range(len(CandidateSegments)):

            i_Video.set(1, CandidateSegments[i][0])
            ret1, frame1 = i_Video.read()

            i_Video.set(1, CandidateSegments[i][1])
            ret1, frame2 = i_Video.read()
            HistDifference = []

            if i == 87:
                print 'a'
            if self.getHist_chi_square(frame1, frame2, wid*hei)>0.5:
                # for j in range(CandidateSegments[i][0], CandidateSegments[i][1]):
                diff = []
                j = CandidateSegments[i][0]
                while j < CandidateSegments[i][1]:
                    diff.append(self.Mnw(j, 0.5))
                    j += 1

                CandidateHardCut = []
                temp1=0
                temp1Index=-1
                temp2=0
                temp2Index=-1
                MinDiff = 1
                # if CandidateSegments[i][0]==1880:
                #     print "test"
                if len([_ for _ in diff if _ > 0.1]) >= len(diff)/2:
                    continue
                for k in range(len(diff)):
                    if diff[k] > 0.5 and temp1 == 0:
                        temp1 = diff[k]
                        temp1Index = k
                    elif diff[k] > 0.5 and temp1 != 0 and np.abs(temp1Index-k) == 1:
                        temp2 = diff[k]
                        temp2Index = k
                    elif diff[k] > 0.5 and temp1 != 0 and np.abs(temp1Index-k) != 1:
                        temp1 = diff[k]
                        temp1Index = k

                    if temp1Index!=-1 and np.abs(temp2-temp1)<1  and np.abs(temp2-temp1)<MinDiff :
                        CandidateHardCut=[CandidateSegments[i][0]+temp1Index, CandidateSegments[i][0]+temp2Index]
                        MinDiff = np.abs(temp2-temp1)
                        temp1 = temp2
                        temp1Index = temp2Index
                        temp2 = 0
                        temp2Index = -1
                    if temp1Index==0 and k==len(diff)-1:
                        temp2 = temp1
                        temp2Index = temp1Index
                        temp1 = self.Mnw(CandidateSegments[i][0]-1,0.5)
                        if np.abs(temp2-temp1)<0.1:
                            Answer.append([CandidateSegments[i][0]-1, CandidateSegments[i][0]])
                    if temp1Index==9 and k==len(diff)-1:
                        temp2 = self.Mnw(CandidateSegments[i][1],0.5)
                        if np.abs(temp2-temp1)<0.1:
                            Answer.append([CandidateSegments[i][1]-1, CandidateSegments[i][1]])

                if len(CandidateHardCut)>0:
                    Answer.append(CandidateHardCut)
                    # i_Video.set(1, j)
                    # ret1_, frame1_ = i_Video.read()
                    #
                    # i_Video.set(1, j+1)
                    # ret2_, frame2_ = i_Video.read()
                    #
                    # HistDifference.append(self.getHist_chi_square(frame1_, frame2_, wid*hei))


                # if np.max(HistDifference) > 2 and np.max(HistDifference) < 5 and len([_ for _ in HistDifference if _ > 2]) == 1:
                #
                #     FrameV = []
                #     FrameV.append(self.get_vector([CandidateSegments[i][0]+np.argmax(HistDifference)]))
                #     FrameV.append(self.get_vector([CandidateSegments[i][-1]+np.argmax(HistDifference)+1]))
                #
                #     cosin = self.getD1(FrameV)
                #
                #     Answer.append([CandidateSegments[i][0]+np.argmax(HistDifference), CandidateSegments[i][0]+np.argmax(HistDifference)+1])
                #
                # elif np.max(HistDifference) >=5 and len([_ for _ in HistDifference if _ > 2]) == 1:
                #     Answer.append([CandidateSegments[i][0]+np.argmax(HistDifference), CandidateSegments[i][0]+np.argmax(HistDifference)+1])
                # elif np.max(HistDifference) > 0.5 and len([_ for _ in HistDifference if _ >0.5]) == 1 and (np.max(HistDifference)/np.max([_ for _ in HistDifference if _ <=0.5]))>=10 :
                #     Answer.append([CandidateSegments[i][0]+np.argmax(HistDifference), CandidateSegments[i][0]+np.argmax(HistDifference)+1])
                # elif np.max(HistDifference) > 0.5 and len([_ for _ in HistDifference if _ >0.5]) == 2 and (np.max(HistDifference)/np.min([_ for _ in HistDifference if _ >0.5])) >10:
                #     Answer.append([CandidateSegments[i][0]+np.argmax(HistDifference), CandidateSegments[i][0]+np.argmax(HistDifference)+1])

            else:
                for p2 in HardCutTruth:
                    if self.if_overlap(CandidateSegments[i][0], CandidateSegments[i][1], p2[0], p2[1]):
                        print 'This cut has been missed : ', p2
            if len(Answer) > 0 and len(Answer) > AnswerLength:
                AnswerLength += 1
                if Answer[-1] not in HardCutTruth:
                    print 'This a false cut'
            else:
                for p in HardCutTruth:
                    if self.if_overlap(CandidateSegments[i][0], CandidateSegments[i][1], p[0], p[1]):
                        print 'This cut has been missed : ', p
                    # Flag = False
                    # for k in HardCutTruth:
                    #     Flag = self.if_overlap(Answer[-1][0], Answer[-1][1], k[0], k[1])
                    #     if Flag:
                    #         break
                    # if Flag is False:
                    #     print 'This is a false cut: ', Answer[-1]

        Miss = 0
        True_ = 0
        False_ = 0
        for i in Answer:
            if i not in HardCutTruth:
                print 'False :', i, '\n'
                False_ = False_ + 1
            else:
                True_ = True_ + 1

        for i in HardCutTruth:
            if i not in Answer:
                Miss = Miss + 1

        print 'False No. is', False_,'\n'
        print 'True No. is', True_, '\n'
        print 'Miss No. is', Miss, '\n'


    # CT Detection base on CNN
    def CTDetection(self):
        import math
        import matplotlib.pyplot as plt
        import numpy as np

        k = 0.4
        Tc = 0.05

        CandidateSegments = self.CutVideoIntoSegments()
        # for i in range(len(CandidateSegments)):
        #     FrameV = self.get_vector(CandidateSegments[i])
        [HardCutTruth, GradualTruth] = self.CheckSegments(CandidateSegments)

        # It save the predicted shot boundaries
        Answer = []

        # It save the candidate segments which may have gradual
        CandidateGra = []

        for i in range(len(CandidateSegments)):
            FrameV = []
            FrameV.append(self.get_vector([CandidateSegments[i][0]]))
            FrameV.append(self.get_vector([CandidateSegments[i][-1]]))

            D1 = self.getD1(FrameV)
            if D1 < 0.9:
                D1Sequence = []

                CandidateFrame = self.get_vector(CandidateSegments[i])
                for j in range(len(CandidateFrame) - 1):
                    D1Sequence.append(self.cosin_distance(CandidateFrame[j], CandidateFrame[j+1]))

                if len([_ for _ in D1Sequence if _ < 0.9]) > 1:
                    CandidateGra.append([CandidateSegments[i][0],CandidateSegments[i][0]+20])
                    continue
                if np.min(D1Sequence) < k*D1+(1-k):
                    if np.max(D1Sequence) - np.min(D1Sequence) >  Tc:
                        Answer.append([CandidateSegments[i][0]+np.argmin(D1Sequence), CandidateSegments[i][0]+np.argmin(D1Sequence)+1])
                    else:
                        CandidateGra.append([CandidateSegments[i][0], CandidateSegments[i][0] + 20])
                else:
                    CandidateGra.append([CandidateSegments[i][0], CandidateSegments[i][0] + 20])

                    #if np.max(D1Sequence)- np.min(D1Sequence) > Tc:
                        #print np.argmin(D1Sequence)


        Miss = 0
        True = 0
        False = 0
        for i in Answer:
            if i not in HardCutTruth:
                print 'False :', i, '\n'
                False = False + 1
            else:
                True = True + 1

        for i in HardCutTruth:
            if i not in Answer:
                Miss = Miss + 1

        print 'False No. is', False,'\n'
        print 'True No. is', True, '\n'
        print 'Miss No. is', Miss, '\n'

        [cut_correct, gradual_correct, all_correct] =self.eval(Answer, HardCutTruth)
        print self.recall_pre_f1(cut_correct, len(HardCutTruth), len(Answer))
            # # plot the image
            #
            # x = range(len(D1Sequence))
            #
            # plt.figure()
            # plt.plot(x, D1Sequence)
            #
            # plt.show()


if __name__ == '__main__':
    test1 = JingweiXu()
    # test1.CTDetection()
    # test1.CutVideoIntoSegments()

    test1.CTDetectionBaseOnHist()