import os
import cv2
import glob
from flask import Flask, render_template, request,redirect, url_for,session
from gevent.pywsgi import WSGIServer
from werkzeug.utils import secure_filename
import pandas as pd
import wgetter
from keras.models import load_model
from sklearn.externals import joblib
from flask import jsonify
import  json



with open('config.json','r') as c:
   params = json.load(c)["params"]

UPLOAD_FOLDER = 'user_uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def check_or_make_folder(foldername):
    if not os.path.exists(foldername):
        os.mkdir(foldername)

check_or_make_folder(UPLOAD_FOLDER)
app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
model = load_model('C:/Users/Ankur/Desktop/Tvaksh-complete-master/Tvaksh-master/saved_models/current_model.h5') #Change to model being used
mapper = joblib.load('C:/Users/Ankur/Desktop/Tvaksh-complete-master/Tvaksh-master/saved_models/current_model_mapping.pkl')
mapper = {v:k for k,v in mapper.items()}

EXTRA_DETAILS_LOCATION = "C:/Users/Ankur/Desktop/Tvaksh-complete-master/Tvaksh-master/disease_extra_details.csv"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/")
def main():
	return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        pic = preprocess_single_image(filepath)
        pred_class = model.predict_classes(pic)[0]
        pred_class_name = get_pred_class_name(pred_class)
        pred_class_extra_details_dic = get_pred_class_extra_details(pred_class_name)
        pred_class_extra_details_dic["Disease"] = pred_class_extra_details_dic["Disease"].replace("%20"," ")
        print("Predicted class is {}".format(pred_class_name))
      
        joblib.dump(pred_class_extra_details_dic,'diseaseinfo.pkl') # Disease information dump in pickle file
        print(pred_class_extra_details_dic)
        if request.method == 'POST':
            return render_template('display.html',dic=pred_class_extra_details_dic)

    
        return jsonify(pred_class_extra_details_dic)
            # display_results(pred_class_extra_details_dic)
            #return ''
            
    return "upload rejected"


@app.route("/display")
def test():
    dic = joblib.load("diseaseinfo.pkl")
    return render_template('display.html',dic=dic)

#       ...............................dispaly function le rha hai ki nhi  values 
# @app.route("/display2")
# def display_results(dic):
#     return render_template('display.html',dic=dic)
    
    
def get_pred_class_extra_details(pred_class_name):
    df = load_and_format_extra_details_csv()
    df = df[df["Disease"] == pred_class_name]
    return df.to_dict(orient='records')[0]
    
def get_pred_class_name(pred_class_number):
    global mapper
    return mapper[pred_class_number]
    
def load_and_format_extra_details_csv():
    global EXTRA_DETAILS_LOCATION
    df = pd.read_csv(EXTRA_DETAILS_LOCATION)
    df["Disease"] = [x.replace(' ','%20') for x in df["Disease"]]
    return df

def preprocess_single_image(filepath):
    pic = cv2.imread(filepath)
    pic = cv2.resize(pic, (120,120))
    pic = pic.astype('float32')
    pic /= 255
    pic = pic.reshape(-1,120,120,3)
    return pic
    

#other routing 



@app.route('/index')
def index():
 # Main page
    return render_template('index.html')


@app.route("/home")
def home():
    if ('user' in session and session ['user'] == params['admin_user']):
        return render_template('home.html')

    else:
        return render_template('register.html')    
	

@app.route('/contactus')
def contactus():

    return render_template('contactus.html')



@app.route('/register', methods = ['GET', 'POST'] )
def register():

   if ('user' in session and session ['user'] == params['admin_user']):
      
      return render_template('home.html',params=params  )

   if request.method == 'POST':
      username = request.form.get('uname')
      userpass = request.form.get('pass')
      if (username == params['admin_user'] and userpass == params['admin_password'] ):
         #set the session variable
         session['user'] = username
         
         return render_template('home.html', params=params )

      #Redirect to Admin Panel
   else:
      return render_template('register.html' ,params=params )

    




@app.route('/about')
def about():

    return render_template('about.html')
   


@app.route('/predict',methods =['GET','POST'] )
def predict():
   
    
    return render_template('result.html')




@app.route('/skinhealth')
def skinhealth():
 
    return render_template('skinhealth.html')
   









if __name__ == "__main__":
    server = WSGIServer(("127.0.0.1",5000), app)
    print('Server is up copy this address and paste in browser url http://127.0.0.1:5000/')
    server.serve_forever()
