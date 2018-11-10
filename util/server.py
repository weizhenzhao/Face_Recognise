import sys
import datetime

from twisted.internet import reactor, ssl
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource
import face_recognition
from PIL import Image
import io
import os
import time
import json


know_user_encoding = []


def load_know_images():
    # load know face image and encode it
    print("know user images load")
    start = time.time()

    imgknow_LiHui = face_recognition.load_image_file("./images/LiHui.png")
    imgknow_LiHui_face_encodings = face_recognition.face_encodings(imgknow_LiHui, num_jitters=5)[0]

    imgknow_dehua = face_recognition.load_image_file("./images/dehua.jpg")
    imgknow_dehua_face_encodings = face_recognition.face_encodings(imgknow_dehua, num_jitters=5)[0]

    imgknow_GuoMeng = face_recognition.load_image_file("./images/GuoMeng.jpg")
    imgknow_GuoMeng_face_encodings = face_recognition.face_encodings(imgknow_GuoMeng, num_jitters=5)[0]

    imgknow_weizhen = face_recognition.load_image_file("./images/weizhen.jpg")
    imgknow_weizhen_face_encodings = face_recognition.face_encodings(imgknow_weizhen, num_jitters=5)[0]

    end = time.time()
    print(time.ctime(), "load_know_images :", end - start)

    imgknow = [imgknow_LiHui_face_encodings,
               imgknow_dehua_face_encodings,
               imgknow_GuoMeng_face_encodings,
               imgknow_weizhen_face_encodings
               ]
    return imgknow



class EchoServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super(WebSocketServerProtocol, self).__init__()



    def onMessage(self, payload, isBinary):
        result = {}
        face_rec_rsult=""
        if isBinary:
            #self.detect_faces_in_image(img_b64decode)
            if len(payload) >0:

                byte_stream = io.BytesIO(payload)

                roiImg = Image.open(byte_stream)
                imgByteArr = io.BytesIO()
                roiImg.save(imgByteArr, format='png')
                imgByteArr = imgByteArr.getvalue()


                now = datetime.datetime.now()
                tempPicturePath = "./"+now.strftime('%Y-%m-%d-%H-%M-%S')+".png"

                tempPicture = open(tempPicturePath, "wb")
                tempPicture.write(imgByteArr)
                tempPicture.close()

                face_rec_rsult = self.detect_faces_in_image(tempPicturePath)
                os.remove(tempPicturePath)
                print("temp picture removed")
            print(face_rec_rsult)
            self.sendMessage(json.dumps(face_rec_rsult).encode(encoding="utf-8"))
        else:
            #print("Text message received: {}".format(payload))
            self.sendMessage(payload)




    def detect_faces_in_image(self,file_stream):
        #load unknow face image and encode it
        imgunknow = face_recognition.load_image_file(file_stream)
        unknown_face_encodings = face_recognition.face_encodings(imgunknow)

        imgknow = know_user_encoding

        known_face_names = [
            "LiHui",
            "Dehua",
            "GuoMeng",
            "WeiZhen"
        ]


        face_found = False
        is_weizhen = False

        face_names = []
        if len(unknown_face_encodings) > 0:
            face_found = True
            # See if the first face in the uploaded image matches the known face of Obama
            start = time.time()
            match_results = face_recognition.compare_faces(imgknow, unknown_face_encodings[0],tolerance=0.45)
            end = time.time()
            print(time.ctime(), "face_recognition_compare_faces : ", end - start)
            print(match_results)
            if True in match_results:
                first_match_index = match_results.index(True)
                name = known_face_names[first_match_index]
                face_names.append(name)


        # Return the result as json
        result = {
            "face_found_in_image": face_names
        }

        return result

if __name__ == '__main__':

    log.startLogging(sys.stdout)

    contextFactory = ssl.DefaultOpenSSLContextFactory('server.key',
                                                      'server.crt')

    factory = WebSocketServerFactory(u"wss://127.0.0.1:9001")
    factory.protocol = EchoServerProtocol

    resource = WebSocketResource(factory)

    # we server static files under "/" ..
    root = File(".")

    # and our WebSocket server under "/ws" (note that Twisted uses
    # bytes for URIs)
    root.putChild(b"ws", resource)

    # both under one Twisted Web Site
    site = Site(root)

    know_user_encoding = load_know_images()

    reactor.listenSSL(9001, site, contextFactory)

    reactor.run()