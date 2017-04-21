import numpy
import indicoio
import easygui
import requests
import os, subprocess
from math import sqrt
from PIL import Image

# Dependencies: numpy, easygui, indicoio, ffmpeg
happy 			= Image.open('emojis/happy.png')
happyPlus 		= Image.open('emojis/happyPlus.png')
sad 			= Image.open('emojis/sad.png')
sadPlus 		= Image.open('emojis/sadPlus.png')
angry 			= Image.open('emojis/angry.png')
angryPlus 		= Image.open('emojis/angryPlus.png')
fear 			= Image.open('emojis/fear.png')
fearPlus 		= Image.open('emojis/fearPlus.png')
surprise 		= Image.open('emojis/suprise.png')
surprisePlus 	= Image.open('emojis/suprisePlus.png')
neutral 		= Image.open('emojis/neutral.png')
neutralPlus 	= Image.open('emojis/neutralPlus.png')
happyFear 		= Image.open('emojis/happy+fear.png')
happySurprise 	= Image.open('emojis/happy+suprised.png')
happyNeutral 	= Image.open('emojis/happy+neutral.png')
sadAngry 		= Image.open('emojis/sad+angry.png')
sadFear 		= Image.open('emojis/sad+fear.png')
sadSurprise 	= Image.open('emojis/sad+suprised.png')
sadNeutral 		= Image.open('emojis/sad+neutral.png')
angryFear 		= Image.open('emojis/angry+fear.png')
angrySurprise 	= Image.open('emojis/angry+suprised.png')
angryNeutral 	= Image.open('emojis/angry+neutral.png')
fearSurprise 	= Image.open('emojis/fear+suprised.png')
fearNeutral 	= Image.open('emojis/neutral+fear.png')
neutralSurprise = Image.open('emojis/neutral+suprised.png')

# Image IndicoData -> None
# Effect: modifies image to include emojis
def pasteEmojis_effectful(img, faceInfo):
	(x1, y1) = faceInfo['location']['top_left_corner']
	(x2, y2) = faceInfo['location']['bottom_right_corner']
	emotions = sorted(faceInfo['emotions'].items(), key=lambda kv: -kv[1])
	first, second = emotions[0], emotions[1]

	if (first[1] + second[1]) / sum(faceInfo['emotions'].values()) >= .5 and second[1] / first[1] > .65: # 2 emotions
		if first[0] in ('Happy','Fear') and second[0] in ('Happy','Fear'):
			emoji = happyFear
		elif first[0] in ('Happy','Surprise') and second[0] in ('Happy','Surprise'):
			emoji = happySurprise
		elif first[0] in ('Happy','Neutral') and second[0] in ('Happy','Neutral'):
			emoji = happyNeutral
		elif first[0] in ('Sad','Angry') and second[0] in ('Sad','Angry'):
			emoji = sadAngry
		elif first[0] in ('Sad','Fear') and second[0] in ('Sad','Fear'):
			emoji = sadFear
		elif first[0] in ('Sad','Surprise') and second[0] in ('Sad','Surprise'):
			emoji = sadSurprise
		elif first[0] in ('Sad','Neutral') and second[0] in ('Sad','Neutral'):
			emoji = sadNeutral
		elif first[0] in ('Angry','Fear') and second[0] in ('Angry','Fear'):
			emoji = angryFear
		elif first[0] in ('Angry','Surprise') and second[0] in ('Angry','Surprise'):
			emoji = angrySurprise
		elif first[0] in ('Angry','Neutral') and second[0] in ('Angry','Neutral'):
			emoji = angryNeutral
		elif first[0] in ('Fear','Surprise') and second[0] in ('Fear','Surprise'):
			emoji = fearSurprise
		elif first[0] in ('Fear','Neutral') and second[0] in ('Fear','Neutral'):
			emoji = fearNeutral
		elif first[0] in ('Neutral','Surprise') and second[0] in ('Neutral','Surprise'):
			emoji = neutralSurprise
		else:
			emoji = neutral

	elif first[1] > 0.60: # strong emotion
		if first[0] == 'Happy':
			emoji = happyPlus
		elif first[0] == 'Sad':
			emoji = sadPlus
		elif first[0] == 'Angry':
			emoji = angryPlus
		elif first[0] == 'Fear':
			emoji = fearPlus
		elif first[0] == 'Surprise':
			emoji = surprisePlus
		else:
			emoji = neutralPlus

	else: # weak emotion
		if first[0] == 'Happy':
			emoji = happy
		elif first[0] == 'Sad':
			emoji = sad
		elif first[0] == 'Angry':
			emoji = angry
		elif first[0] == 'Fear':
			emoji = fear
		elif first[0] == 'Surprise':
			emoji = surprise
		else:
			emoji = neutral

	emoji = emoji.resize((x2-x1, y2-y1))
	img.paste(emoji, (x1,y1), emoji)


# [ImgInfo] Int Int -> None
def smoothenFaces(imgInfos, w, h):
	if not imgInfos:
		return None

	for i in range(2, len(imgInfos) - 2):
		for faceInfo in imgInfos[i]:
			x1, y1 = faceInfo['location']['top_left_corner']
			x2, y2 = faceInfo['location']['bottom_right_corner']

			prevIndex = getNearbyFace((x1 + x2)/2, (y1 + y2)/2, w, h, imgInfos[i-1], x2-x1, y2-y1)
			nextIndex = getNearbyFace((x1 + x2)/2, (y1 + y2)/2, w, h, imgInfos[i+1], x2-x1, y2-y1)

			adjs = []
			if prevIndex is not None: adjs.append(imgInfos[i-1][prevIndex])
			adjs.append(faceInfo)
			if nextIndex is not None: adjs.append(imgInfos[i+1][nextIndex])

			def x1(fInfo): return fInfo['location']['top_left_corner'][0]
			def y1(fInfo): return fInfo['location']['top_left_corner'][1]
			def x2(fInfo): return fInfo['location']['bottom_right_corner'][0]
			def y2(fInfo): return fInfo['location']['bottom_right_corner'][1]
			length = len(adjs)

			xAvg = sum((x1(fInfo) + x2(fInfo)) / 2 for fInfo in adjs) / length
			yAvg = sum((y1(fInfo) + y2(fInfo)) / 2 for fInfo in adjs) / length
			wAvg = sum( x2(fInfo) - x1(fInfo) 	   for fInfo in adjs) / length
			hAvg = sum( y2(fInfo) - y1(fInfo) 	   for fInfo in adjs) / length

			x1, y1 = xAvg - wAvg/2, yAvg - hAvg/2
			x2, y2 = xAvg + wAvg/2, yAvg + hAvg/2

			faceInfo['location']['top_left_corner'] 	= int(x1), int(y1)
			faceInfo['location']['bottom_right_corner'] = int(x2), int(y2)

			for emotion in ('Happy', 'Sad', 'Angry', 'Fear', 'Surprise', 'Neutral'):
				avg = sum(fInfo['emotions'][emotion] for fInfo in adjs) / length
				faceInfo[emotion] = avg


# Int Int Int Int ImgInfo -> Maybe Int
# returns index of nearby face, or None if none exists
def getNearbyFace(x, y, w, h, imgInfo, prevW, prevH):
	if not imgInfo:
		return None

	for i, faceInfo in enumerate(imgInfo):
		if not faceInfo:
			continue

		(x1,y1) = faceInfo['location']['top_left_corner']
		(x2,y2) = faceInfo['location']['bottom_right_corner']
		dx = abs(x - (x1+x2)/2)
		dy = abs(y - (y1+y2)/2)

		wRatio = (x2-x1) / prevW
		hRatio = (y2-y1) / prevH

		if dx < w / 10 and dy < h / 10 and 0.8 < wRatio < 1.2 and 0.8 < hRatio < 1.2:
			return i


# [String] -> [Image]
# Effect: Calls the Indico API
def urlsToImages(imgUrls):
	denom = len(imgUrls)
	imgInfos = []
	i = 0

	for i, url in enumerate(imgUrls):
		try:
			imgInfo = indicoio.fer(url, detect=True)
			imgInfos.append(imgInfo)
			i += 1
			print('%d / %d' % (i, denom))

		except indicoio.utils.errors.IndicoError:
			imgInfos.append({})
			i += 1
			print('%d / %d' % (i, denom))

		except requests.exceptions.ConnectionError:
			pass

	print('Smoothening...')
	imgs = [ Image.open(url) for url in imgUrls ]

	smoothenFaces(imgInfos, imgs[0].size[0], imgs[0].size[1])
	# with Image.open(imgUrls[0]) as first:
	# 	smoothenFaces(imgInfos, first.size[0], first.size[1])

	print('Adding emojis...')
	for img, imgInfo in zip(imgs, imgInfos):
		for faceInfo in imgInfo:
			pasteEmojis_effectful(img, faceInfo)

	return imgs

# GifURL -> [Image]
# Effect: Calls the Indico API
def gifUrlToFrames(url):
	gif = Image.open(url)
	imgs = []
	i = 0

	try:
		while 1:
			gif.seek(i)
			frame = gif.copy()

			w, h = frame.size
			if w % 2: w -= 1
			if h % 2: h -= 1
			frame = frame.crop((0, 0, w, h)).convert('RGB')

			try:
				imgInfo = indicoio.fer(numpy.array(frame), detect=True)
				[ pasteEmojis_effectful(frame, faceInfo) for faceInfo in imgInfo ]
				imgs.append(frame)
				i += 1
			except indicoio.utils.errors.IndicoError: 
				imgs.append(frame)
				i += 1
			except requests.exceptions.ConnectionError:
				pass

	except EOFError:
		return imgs


# String -> None
# Effect: saves gif frames to /output
# Effect: creates an mp4 of a gif and saves it in /output
def processGifUrl_effectful(url):
	framerate = Image.open(url).info['duration'] / 1000.0
	gifName = url.split('/')[-1].split('\\')[-1].split('.')[0]
	frames = gifUrlToFrames(url)

	if not os.path.exists('Output/' + gifName):
		os.makedirs('Output/' + gifName)

	[ frame.save('Output/%s/%003d.png' % (gifName, i)) for i, frame in enumerate(frames) ]

	subprocess.Popen('ffmpeg -framerate %d -i Output/%s/%%003d.png -c:v libx264 -r 30 -pix_fmt yuv420p Output/%s.mp4' 
			% (1/framerate, gifName, gifName))


def processMovieUrl_effectful(url):
	movieName = url.split('/')[-1].split('\\')[-1].split('.')[0]

	if not os.path.exists('Input/' + movieName):
		os.makedirs('Input/' + movieName)
	if not os.path.exists('Output/' + movieName):
		os.makedirs('Output/' + movieName)

	# movie to frames
	subprocess.call('ffmpeg -i ' + url + ' -vf fps=10 Input/' + movieName + '/%09d.png', shell=True)

	# movie to audio
	subprocess.call('ffmpeg -ss 0 -i ' + url + ' Output/' + movieName + '/audio.mp3', shell=True)

	i = 1
	urls = []
	while os.path.isfile('Input/%s/%09d.png' % (movieName, i)):
		urls.append('Input/%s/%09d.png' % (movieName, i))
		i += 1

	frames = urlsToImages(urls)

	for url, frame in zip(urls, frames):
		url = url.split('/')[-1].split('\\')[-1]
		# frame.save('Output/' + movieName + '/' + url)
		frame.save('Output/%s/%s' % (movieName, url))

	# frames to movie
	# call_command('ffmpeg -framerate 10 -i Output/' + movieName + '/%09d.png -c:v libx264 -r 30 -pix_fmt yuv420p Output/' + movieName + '/_' + movieName + '_.mp4')
	subprocess.call('ffmpeg -framerate 10 -i Output/%s/%%09d.png -c:v libx264 -r 30 -pix_fmt yuv420p Output/%s/_%s_.mp4' % (movieName, movieName, movieName))

	# merge video and audio
	# call_command('ffmpeg -i Output/' + movieName + '/_' + movieName + '_.mp4 -i Output/' + movieName + '/audio.mp3 -codec copy -shortest Output/' + movieName + '.mp4')
	subprocess.call('ffmpeg -i Output/%s/_%s_.mp4 -i Output/%s/audio.mp3 -codec copy -shortest Output/%s.mp4' % (movieName, movieName, movieName, movieName))




if __name__ == '__main__':
	requests.packages.urllib3.disable_warnings()
	indicoio.config.api_key = '<redacted>'

	fileNameAndPath = easygui.fileopenbox(title='Choose your file:',
										  filetypes=('*.mp4', '*.mkv', '*.png', '*.jpeg', '*.jpg', '*.bmp', '*.gif'))

	videoTypes = ['mp4', 'mkv']
	picTypes = ['png', 'jpeg', 'jpg', 'bmp']

	if fileNameAndPath is None:
		raise SystemExit

	fileTypeCheck = fileNameAndPath.split('.')[-1]

	if fileTypeCheck == 'gif':
		processGifUrl_effectful(fileNameAndPath)

	elif fileTypeCheck in videoTypes:
		processMovieUrl_effectful(fileNameAndPath)

	elif fileTypeCheck in picTypes:
		img = urlsToImages([fileNameAndPath])[0]
		img.save('Output/' + fileNameAndPath.split('/')[-1].split('\\')[-1])
