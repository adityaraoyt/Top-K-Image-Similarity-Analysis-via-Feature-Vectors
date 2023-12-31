import torch
from torchvision import datasets, models
import torchvision
import torchvision.transforms as transforms
from PIL import Image, ImageOps
import matplotlib.pyplot as plt
import scipy
import numpy as np
import cv2
import pandas as pd
import math
from sklearn.metrics import mean_squared_error

data = datasets.Caltech101(root='data', download=True)

"""#### Color Moments"""

def colorMoments(image, color_moments):
    for i in range(0,image.shape[0],10):
        for j in range(0,image.shape[1],30):
            grid_cell = image[i:i+10, j:j+30]
            for k in range(3):
                channel_mean = np.mean(grid_cell[:,:,k])
                channel_std = np.std(grid_cell[:,:,k])
                channel_skew = scipy.stats.skew(grid_cell[:,:,k].flatten())

                color_moments[i//10,j//30,k,:] = [channel_mean,channel_std,channel_skew]

    color_moments.resize(900,)
    return color_moments

CM = []

for i in range(len(data)):
    image, label = data[i]
    image = image.resize((300,100))
    image = np.asarray(image)
    if len(image.shape) != 3:
        image = cv2.merge((image,image,image))
    color_moments = np.zeros((10, 10, 3, 3))
    temp = colorMoments(image, color_moments)
    temp = temp.tolist()
    temp.insert(0,i)
    CM.append(temp)

df = pd.DataFrame(color_moments_list)
df.to_csv('color_moments.csv',index=False,columns=None)

"""#### Histograms of Oriented Gradients"""

def Histogram_of_Oriented_Gradients(image_gs, hog):
    for i in range(0,image_gs.shape[0],10):
        for j in range(0,image_gs.shape[1],30):
            grid_cell = image_gs[i:i+10, j:j+30]
            gx = cv2.Sobel(grid_cell, cv2.CV_32F, 1, 0, ksize=1)
            gy = cv2.Sobel(grid_cell, cv2.CV_32F, 0, 1, ksize=1)
            mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
            hog[i//10, j//30, :] = list(np.histogram(angle,9,(0,360), weights=mag)[0])

    hog.resize(900,)
    return hog

HOG = []

for i in range(len(data)):
    image, label = data[i]
    image = image.resize((300,100))
    image_arr = np.asarray(image)
    if len(image_arr.shape) == 3:
        image_gs = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY)
    else:
        image_arr = cv2.merge((image_arr,image_arr,image_arr))
        image_gs = image_arr
    image_gs = np.float32(image_gs) / 255.0
    hog = np.zeros((10,10,9))
    temp = Histogram_of_Oriented_Gradients(image_gs, hog)
    temp = temp.tolist()
    temp.insert(0,i)
    HOG.append(temp)

df = pd.DataFrame(HOG)
df.to_csv('hog.csv',index=False,header=False)

"""#### ResNet Avg-Pool 1024"""

def resnet_avg_1024(image):
    # Load a pre-trained ResNet model
    resnet_model = models.resnet50(pretrained=True)
    # resnet_model = nn.Sequential(*list(resnet_model.children())[:-2])

    # Set the model to evaluation mode (no gradient computation)
    resnet_model.eval()

    # Resize the image to 224x224 and apply necessary transformations
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)  # Add batch dimension

    # Define a hook to get the output of the "fc" layer
    with torch.no_grad():
        my_output = None

        def my_hook(module_, input_, output_):
            nonlocal my_output
            my_output = output_

        a_hook = resnet_model.avgpool.register_forward_hook(my_hook)
        resnet_model(input_batch)
        a_hook.remove()
        my_output = my_output.squeeze().numpy()
        return my_output

AvgPool1024 = []
for d in range(len(data)):

    image, label = data[d]
    if len(np.asarray(image).shape) != 3:
        image = image.convert("RGB")
    avg_1024 = resnet_avg_1024(image)

    v1024 = []
    for i in range(0,len(avg_1024),2):
        v1024.append((avg_1024[i] + avg_1024[i+1]) / 2)

    v1024.insert(0,d)

    AvgPool1024.append(v1024)

df = pd.DataFrame(AvgPool1024)
df.to_csv('AvgPool.csv',index=False,header=None)

"""#### ResNet FC 1000"""

def resnet_fc(image):
    # Load a pre-trained ResNet model
    resnet_model = models.resnet50(pretrained=True)
    # resnet_model = nn.Sequential(*list(resnet_model.children())[:-2])

    # Set the model to evaluation mode (no gradient computation)
    resnet_model.eval()

    # Resize the image to 224x224 and apply necessary transformations
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)  # Add batch dimension

    # Define a hook to get the output of the "fc" layer
    with torch.no_grad():
        my_output = None

        def my_hook(module_, input_, output_):
            nonlocal my_output
            my_output = output_

        a_hook = resnet_model.fc.register_forward_hook(my_hook)
        resnet_model(input_batch)
        a_hook.remove()
        my_output = my_output.squeeze().numpy()
        return my_output

FC = []
for d in range(len(data)):
    # print(d)
    image, label = data[d]
    if len(np.asarray(image).shape) != 3:
        image = image.convert("RGB")
    fc_1000 = resnet_fc(image)
    fc_1000 = fc_1000.tolist()
    fc_1000.insert(0,d)
    FC.append(fc_1000)

df = pd.DataFrame(FC)
df.to_csv('FullyConnected.csv',index=False,header=False)

"""#### ResNet Layer-3 1024"""

def resnet_layer3_1024(image):
    # Load a pre-trained ResNet model
    resnet_model = models.resnet50(pretrained=True)
    # resnet_model = nn.Sequential(*list(resnet_model.children())[:-2])

    # Set the model to evaluation mode (no gradient computation)
    resnet_model.eval()

    # Resize the image to 224x224 and apply necessary transformations
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)  # Add batch dimension

    # Define a hook to get the output of the "fc" layer
    with torch.no_grad():
        my_output = None

        def my_hook(module_, input_, output_):
            nonlocal my_output
            my_output = output_

        a_hook = resnet_model.layer3.register_forward_hook(my_hook)
        resnet_model(input_batch)
        a_hook.remove()
        my_output = my_output.squeeze().numpy()
        return my_output

Layer3 = []
for d in range(len(data)):
    # print(d)
    image, label = data[d]
    if len(np.asarray(image).shape) != 3:
        image = image.convert("RGB")
    layer3_1024 = resnet_layer3_1024(image)
    avg_slice = []
    for i in range(layer3_1024.shape[0]):
        avg_slice.append(np.mean(layer3_1024[i,:,:]))

    avg_slice.insert(0,d)
    Layer3.append(avg_slice)

df = pd.DataFrame(Layer3)
df.to_csv('Layer3.csv',index=False,header=False)

"""#### Retrieval"""

def L2_norm(df, target_vec, k):
    l2 = {}
    for i in df[0]:
        temp_df = df.loc[df[0] == i,1:]
        temp_idx = df.loc[df[0] == i,1:].index[0]
        source_vec = list(df.loc[df[0] == i,1:].loc[temp_idx])
        dist = math.dist(source_vec, target_vec)
        if len(l2) <= k:
            l2[i] = dist
        else:
            l2Zip = max(zip(l2.values(), l2.keys()))
            keymax = l2Zip[1]
            if dist < l2Zip[0]:
                del l2[keymax]
                l2[i] = dist

    for i in l2.keys():
        data[i][0].save(f'K images/img{i}.jpg')

def Cosine(df, target_vec, k):
    cos = {}
    for i in df[0]:
        temp_df = df.loc[df[0] == i,1:]
        temp_idx = df.loc[df[0] == i,1:].index[0]
        source_vec = list(df.loc[df[0] == i,1:].loc[temp_idx])
        dist = np.dot(source_vec, target_vec)/(np.linalg.norm(source_vec) * np.linalg.norm(target_vec))
        if len(cos) <= k:
            cos[i] = dist
        else:
            cosZip = min(zip(cos.values(), cos.keys()))
            keymin = cosZip[1]
            if dist > cosZip[0]:
                del cos[keymin]
                cos[i] = dist

    for i in cos.keys():
        data[i][0].save(f'K images/img{i}.jpg')

    print(cos)

def MSE(df, target_vec, k):
    mse = {}
    for i in df[0]:
        temp_df = df.loc[df[0] == i,1:]
        temp_idx = df.loc[df[0] == i,1:].index[0]
        source_vec = list(df.loc[df[0] == i,1:].loc[temp_idx])
        dist = np.dot(source_vec, target_vec)/(np.linalg.norm(source_vec) * np.linalg.norm(target_vec))
        if len(mse) <= k:
            mse[i] = dist
        else:
            mseZip = max(zip(mse.values(), mse.keys()))
            keymax = mseZip[1]
            if dist < mseZip[0]:
                del mse[keymax]
                mse[i] = dist

    for i in mse.keys():
        data[i][0].save(f'K images/img{i}.jpg')

    print(mse)

while True:
    id = int(input("Enter Image id: "))
    if id>=0 and id<8677:
        break

while True:
    m = int(input('\n\n1. Color Moments\n\n2. HOG\n3. ResNet Avg Pool\n4. ResNet Fully Connected\n5. ResNet Layer-3\n\n'))
    if m>=1 and m<=5:
        break

k = int(input("Enter k"))

if m == 1:
    df = pd.read_csv("color_moments.csv", header=None)
    df.fillna(0)
    image, label = data[id]
    image = image.resize((300, 100))
    image = np.asarray(image)
    if len(image.shape) != 3:
        image = cv2.merge((image, image, image))
    color_moments = np.zeros((10, 10, 3, 3))
    vec = colorMoments(image, color_moments)
    vec = vec.tolist()
    # print(vec)
    L2_norm(df, vec, k)

elif m == 2:
    df = pd.read_csv("hog.csv", header=None)
    image, label = data[id]
    image = image.resize((300, 100))
    image_arr = np.asarray(image)
    if len(image_arr.shape) == 3:
        image_gs = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY)
    else:
        image_arr = cv2.merge((image_arr, image_arr, image_arr))
        image_gs = image_arr
    image_gs = np.float32(image_gs) / 255.0
    hog = np.zeros((10, 10, 9))
    vec = Histogram_of_Oriented_Gradients(image_gs, hog)
    vec = vec.tolist()

    Cosine(df, vec, k)

elif m == 3:
    df = pd.read_csv("AvgPool.csv", header=None)
    image, label = data[id]
    if len(np.asarray(image).shape) == 3:
        avg_1024 = resnet_avg_1024(image)

        v1024 = []
        for i in range(0, len(avg_1024), 2):
            v1024.append((avg_1024[i] + avg_1024[i + 1]) / 2)

        Cosine(df, v1024, k)

elif m == 4:
    df = pd.read_csv("FullyConnected.csv", header=None)
    image, label = data[id]
    if len(np.asarray(image).shape) == 3:
        fc_1000 = resnet_fc(image)
        fc_1000 = fc_1000.tolist()

        Cosine(df, fc_1000, k)

elif m == 5:
    df = pd.read_csv("Layer3.csv", header=None)
    image, label = data[id]
    if len(np.asarray(image).shape) == 3:
        layer3_1024 = resnet_layer3_1024(image)
        avg_slice = []
        for i in range(layer3_1024.shape[0]):
            avg_slice.append(np.mean(layer3_1024[i, :, :]))

        Cosine(df, avg_slice, k)

data[id][0]





