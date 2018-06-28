
'''
the part oder:
0:nose         1:neck           2:right_shoulder   3:right_elbow
4:right_wrist  5:left_shoulder  6:left_elbow       7:left_wrist
8:right_hip    9:right_knee     10:right_ankle    11:left_hip
12:left_knee   13:left_ankle    14:right_eye       15:left_eye
16:right_ear   17:left_ear
'''

class Point:
    def __init__(self, coord):
        self.x = coord[0] if len(coord) > 0 else None
        self.y = coord[1] if len(coord) > 0 else None

class Frame:
    def __init__(self, peaks, img):
        self.peaks = peaks
        self.img = img
        self.status = ""

        self.tips = []

        self.nose = Point(self.peaks[0])
        self.neck = Point(self.peaks[1])
        self.r_shoulder = Point(self.peaks[2])
        self.r_elbow = Point(self.peaks[3])
        self.r_wrist = Point(self.peaks[4])
        self.l_shoulder = Point(self.peaks[5])
        self.l_elbow = Point(self.peaks[6])
        self.l_wrist = Point(self.peaks[7])
        self.r_hip = Point(self.peaks[8])
        self.r_knee = Point(self.peaks[9])
        self.r_ankle = Point(self.peaks[10])
        self.l_hip = Point(self.peaks[11])
        self.l_knee = Point(self.peaks[12])
        self.l_ankle = Point(self.peaks[13])
        self.r_eye = Point(self.peaks[14])
        self.l_eye = Point(self.peaks[15])
        self.r_ear = Point(self.peaks[16])
        self.l_ear = Point(self.peaks[17])

    def set_status(self, status):
        self.status = status

    def is_status(self, status):
        return self.status == status

