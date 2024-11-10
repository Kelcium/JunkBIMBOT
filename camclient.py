import cv2

class Camera():

    def __init__(self):
        self.cam = cv2.VideoCapture(0)

    def take_pic(self, out_path):
        cv2.namedWindow("test")

        while True:
            ret, frame = self.cam.read()
            if not ret:
                print("failed to grab frame")
                break
            cv2.imshow("test", frame)

            k = cv2.waitKey(1)
            if k%256 == 27:
                # ESC pressed
                print("Escape hit, closing...")
                break
            elif k%256 == 32:
                # SPACE pressed
                img_name = out_path
                cv2.imwrite(img_name, frame)
                print("{} written!".format(img_name))
                break
        self.cam.release()
        cv2.destroyAllWindows()
        return
    
if __name__ == '__main__':
    test = Camera()
    test.take_pic('JunctionBIMBOT/test_img.png')