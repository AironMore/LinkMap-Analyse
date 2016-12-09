#!/usr/bin/python
#coding:utf-8

#这个脚本是为了分析linkMap的文件大小
#代码参考 https://github.com/sumx/LinkMapReader
#

import os,sys,shutil
import xlsxwriter   # xlsxwriter 用户生成xlsx文件
from string import Template

class linkFile:
	#定义基本属性
	name = ''
	size = 0
	diff = 0
	#定义构造方法
	def __init__(self,n,s,d):
		self.name = n
		self.size = s
		self.diff = d

	def show(self):
		print("name: %s size: %d diff: %d" %(self.name,self.size,self.diff))

class SymbolReader(object):

	def __init__(self, linkmapdir):
		super(SymbolReader, self).__init__()
		self.linkmapdir=linkmapdir

	#read objs From linkmapdir
	def readObjectFrom(self):
		f=open(self.linkmapdir, "r")
		shouldSkip=True
		dic={}
		for line in f:
			if line.find("Object files:")!=-1 and shouldSkip:
				shouldSkip=False
				continue
			else:
				if line.find("# Sections:")!=-1:
					break
				else:
					objInfo=line.split(']')
					if len(objInfo)==2:
						index=objInfo[0]+']'
						name=objInfo[1]
						dic[index.strip()]=name.strip()
		f.close
		return dic

	#read linkmapdir
	def readSymbolsInfoFrom(self):
		f=open(self.linkmapdir, "r")
		shouldSkip=0
		dic={}
		for line in f:
			if line.find("# Address	Size    	File  Name")!=-1 and  shouldSkip==0:
				shouldSkip=1
				continue
			else:
				if shouldSkip==1:
					symbolInfo=line.split("	")
					if len(symbolInfo)==3:
						offset=symbolInfo[0].strip()
						symbolSize=symbolInfo[1].strip()
						leftStr=symbolInfo[2]
						indexAndSymbolName=leftStr.split('] ')
						if len(indexAndSymbolName) >= 2:
							index=indexAndSymbolName[0]+"]".strip()
							symbolName=indexAndSymbolName[1].strip()
							if index in dic:
								dic[index].append({"Address":offset,"size":symbolSize,"index":index,"name":symbolName})
							else:
								dic[index]=[];
								dic[index].append({"Address":offset,"size":symbolSize,"index":index,"name":symbolName})
		f.close
		return dic

	def generateSymbolSize(self,item):
		sum=0
		for sinfo in item:
			sum=sum+int(sinfo["size"],16)
		return sum

	def generateObjSizeDetail(self):
		objs=self.readObjectFrom()
		symbols=self.readSymbolsInfoFrom()
		tsum=0
		# outFile=open(os.getcwd()+"/result.txt",'w')
		tempArr = []
		for key in sorted(symbols.keys()):
			item=symbols[key]
			tsum=tsum+self.generateSymbolSize(item)
			sum=0
			for sinfo in item:
				sum=sum+int(sinfo["size"],16)
			objNameSplited=objs[key].split(os.sep)
			linkfile = linkFile(objNameSplited[len(objNameSplited)-1], sum, 0)
			tempArr.append(linkfile)
			# print("%s size: %d" %(linkfile.name,linkfile.size))
			# text = "Name: "+objNameSplited[len(objNameSplited)-1]+"/*****/Size: "+str(sum)+"\n"
			# outFile.write(text)
		# outFile.write("all linked size:"+str(tsum))
		print "linkMap analyze has Done!"
		return tempArr

def analyzeLinkMap(dir):
	if os.path.isfile(dir) == True:
		reader=SymbolReader(dir)
		fileArr = reader.generateObjSizeDetail()
		# for linkfile in fileArr:
		# 	print linkfile.name + "======" + str(linkfile.size)
		return fileArr
	else:
		print "should config linkmap path"
		sys.exit(0)

#排序用的方法
def sizeSort(a,b):
	if isinstance(a, linkFile) and isinstance(b, linkFile):
		if int(a.size) < int(b.size):
			return 1
		if int(a.size) > int(b.size):
				return -1
	return 0

def diffSort(a,b):
	if isinstance(a, linkFile) and isinstance(b, linkFile):
		if int(a.diff) < int(b.diff):
				return 1
		if int(a.diff) > int(b.diff):
			return -1
	return 0


#数组去重
def  deplicateArr(oldArr):
	newArr = []
	for oldId in oldArr:
		if oldId not in newArr:
			if isinstance(oldId, linkFile):
				isContain = False
				for newId in newArr:
					if isinstance(newId, linkFile):
						if oldId.name == newId.name and oldId.size == newId.size:
							isContain = True
				if not isContain:
					newArr.append(oldId)
	return newArr


#分析并输出两次迭代的变化
def diffArray(oldArr,newArr,dirName,moduleName):

	workbook = xlsxwriter.Workbook(dirName)
	worksheet = workbook.add_worksheet()

	worksheet.set_column('A:A',60)    #设定列的宽度为60像素
	worksheet.set_column('B:B',10)
	worksheet.set_column('C:C',10)

	currentRow = 0
	title = ''
	worksheet.write(currentRow, 0, 'Name')
	worksheet.write(currentRow, 1, 'Size')
	worksheet.write(currentRow, 2, 'Diff')

	#用来取差集 来找出新增/删除 的文件
	oldCommonArr = []
	newCommonArr = []

	sortArr = []  #用来排序用的数组
	tempArr = []  #没去重的数组
	for oldFile in oldArr:
		for newFile in newArr:
			if oldFile.name == newFile.name:
				oldCommonArr.append(oldFile)
				newCommonArr.append(newFile)
				commonfile = linkFile(newFile.name, newFile.size, newFile.size - oldFile.size)
				tempArr.append(commonfile)

	sortArr = deplicateArr(tempArr)
	oldCommonArr = deplicateArr(oldCommonArr)
	newCommonArr = deplicateArr(newCommonArr)

	totalOldSize = 0
	totalNewSize = 0
	for oldFile in oldArr:
		totalOldSize += int(oldFile.size)

	for  newFile in newArr:
		totalNewSize += int(newFile.size)

	format_title_add = workbook.add_format()    #定义format_title格式对象
	format_title_add.set_border(1)   #定义format_title对象单元格边框加粗(1像素)的格式
	format_title_add.set_bg_color('#ef7175')   #定义format_title对象单元格背景颜色为'#cccccc'的格式

	format_title_del = workbook.add_format()    #定义format_title格式对象
	format_title_del.set_border(1)   #定义format_title对象单元格边框加粗(1像素)的格式
	format_title_del.set_bg_color('#23b6e7')   #定义format_title对象单元格背景颜色为'#cccccc'的格式

	format_title_topTen = workbook.add_format()    #定义format_title格式对象
	format_title_topTen.set_border(1)   #定义format_title对象单元格边框加粗(1像素)的格式
	format_title_topTen.set_bg_color('#fea976')   #定义format_title对象单元格背景颜色为'#cccccc'的格式

	format_title_change = workbook.add_format()    #定义format_title格式对象
	format_title_change.set_border(1)   #定义format_title对象单元格边框加粗(1像素)的格式
	format_title_change.set_bg_color('#cff7d5')   #定义format_title对象单元格背景颜色为'#cccccc'的格式

	currentRow = currentRow + 2
	title =  'old totalSize is ' + str(totalOldSize ) + ' new totalSize is ' + str(totalNewSize) + ' has Changed ' + str(totalNewSize - totalOldSize)
	print("%s: 上次迭代大小为%.2fkb ,此次迭代大小为%.2fkb, 变化了%2.fkb" %(dirName, totalOldSize / 1024, totalNewSize / 1024 , (totalNewSize - totalOldSize) / 1024) )
	resultStr = 'moduleName:' + moduleName + ',lastSize:' + str(totalOldSize / 1024) + ',currentSize:' + str(totalNewSize / 1024)
	worksheet.write(currentRow, 0, title)

	# 新增的文件
	addArr = list(set(newArr).difference(set(newCommonArr))) # newrr中有而newCommonArr中没有的

	currentRow = currentRow + 2
	title =  'Add total ' + str(len(addArr)) + ' files'
	worksheet.write(currentRow, 0, title)
	for addFile in addArr:
		currentRow = currentRow + 1
		worksheet.write(currentRow, 0, str(addFile.name),format_title_add)
		worksheet.write_number(currentRow, 1, int(addFile.size),format_title_add)
		worksheet.write_number(currentRow, 2, int(addFile.size),format_title_add)

	# 被删除的文件
	delArr = list(set(oldArr).difference(set(oldCommonArr))) # oldArr中有而oldCommonArr中没有的

	currentRow = currentRow + 2
	title = 'delete total ' + str(len(delArr)) + ' files'
	worksheet.write(currentRow, 0, title)

	for delFile in delArr:
		currentRow = currentRow + 1
		worksheet.write(currentRow, 0, delFile.name,format_title_del)
		worksheet.write_number(currentRow, 1, int(delFile.size),format_title_del)
		worksheet.write_number(currentRow, 2, 0 - int(delFile.size),format_title_del)

	if len(sortArr) > 10 :
		#按大小排序
		currentRow = currentRow + 2
		worksheet.write(currentRow, 0, "the Size Top10")
		sortArr.sort(cmp = sizeSort)

		for x in xrange(1,10):
			item = sortArr[x]
			currentRow = currentRow + 1
			worksheet.write(currentRow, 0, item.name, format_title_topTen)
			worksheet.write_number(currentRow, 1, int(item.size), format_title_topTen)
			worksheet.write_number(currentRow, 2, int(item.diff), format_title_topTen)

		#按变化排序
		currentRow = currentRow + 2
		worksheet.write(currentRow, 0, "the Change Top10")
		sortArr.sort(cmp = diffSort)

		for x in xrange(1,10):
			item = sortArr[x]
			currentRow = currentRow + 1
			worksheet.write(currentRow, 0, item.name, format_title_topTen)
			worksheet.write_number(currentRow, 1, int(item.size), format_title_topTen)
			worksheet.write_number(currentRow, 2, int(item.diff), format_title_topTen)

	currentRow = currentRow + 2
	title = 'all the ' + str(len(sortArr)) + ' Change files'
	worksheet.write(currentRow, 0, title)

	for row_date in sortArr:
		currentRow = currentRow + 1
		worksheet.write(currentRow, 0, row_date.name, format_title_change)
		worksheet.write_number(currentRow, 1, int(row_date.size), format_title_change)
		worksheet.write_number(currentRow, 2, int(row_date.diff), format_title_change)

	#print dirName + 'Excel is ok!'
	workbook.close()
	return resultStr


def getTheArr(arr, startStrArr):
	theArr = []
	for file in arr :
		for startStr in startStrArr :
			fileName = str(file.name)
			if fileName.count(startStr) > 0:
				theArr.append(file)

	return theArr

def getTheReport(oldArr, newArr, startStrArr, fileName, moduleName):
	oldAirArr = getTheArr(oldArr, startStrArr)
	newAirArr = getTheArr(newArr, startStrArr)
	fileName = os.path.split(os.path.realpath(__file__))[0] + '/LinkMapOutPut/' + fileName #脚本所在位置的目录
	#fileName = '/Users/server/Desktop/linkMapTest/' + '/LinkMapOutPut/' + fileName  #服务器上写死的地址
	resultStr = diffArray(oldAirArr, newAirArr, fileName, moduleName)
	return resultStr

if __name__=='__main__':
	if len(sys.argv) < 2:
		print 'Not enough Params'
		sys.exit(0)


	oldDir = sys.argv[1]
	newDir = sys.argv[2]

	if not os.path.isfile(newDir) :
		print 'No valid new File'
		sys.exit(0)

	cpuTypeSTr = ''
	if newDir.count('arm64') > 0:
		cpuTypeSTr = '-arm64'
	elif newDir.count('-armv7') > 0:
		cpuTypeSTr = '-armv7'
	else:
		pass

	if not os.path.isfile(oldDir):
		print 'No valid old File'
		if os.path.isfile(newDir) :
			shutil.move(newDir,'/Users/server/Desktop/linkMapTest/new/TuNiuApp-LinkMap-normal' + cpuTypeSTr + '.txt') #将新的linkMap文件放入旧的中，替换掉（用来自动化执行）
			print 'had moved New Dir 2 Old Dir'
		sys.exit(0)

	oldArr = analyzeLinkMap(oldDir)
	newArr = analyzeLinkMap(newDir)
	resultStrArr = []

	infoTxt = open(os.path.split(os.path.realpath(__file__))[0] + '/linkMapInfo.txt','rw')
	for line in  infoTxt.readlines():
		print  line
		infoArr = line.split(':')
		if len(infoArr) >= 2:
			print infoArr
			nameStr = infoArr[0]
			startStrArr = ['']
			startStr = infoArr[1]
			startStr = startStr.strip('\n')
			if startStr == 'all':
				startStrArr = ['']
			elif ',' in startStr:
				startStrArr = startStr.split(',')
			else:
				startStrArr = [startStr]

			resultStrArr.append(getTheReport(oldArr, newArr, startStrArr, nameStr + cpuTypeSTr + '.xlsx', nameStr))

	# totalStrArr = ['']
	# resultStrArr.append(getTheReport(oldArr, newArr, totalStrArr, 'totalLinkMap' + cpuTypeSTr + '.xlsx', 'total'))
	#
	# airPlaneStartStrArr = ['TNGAirplane', 'TNAirplane', 'TNIntlFlightTicket']
	# resultStrArr.append(getTheReport(oldArr, newArr, airPlaneStartStrArr, 'airplaneLinkMap' + cpuTypeSTr + '.xlsx', 'airPlane'))
	#
	# trainStartStrArr = ['TNTrain']
	# resultStrArr.append(getTheReport(oldArr, newArr, trainStartStrArr, 'trainLinkMap' + cpuTypeSTr + '.xlsx', 'train'))
	#
	# hotelStartStrArr = ['TNHotel', 'TNGHotel']
	# resultStrArr.append(getTheReport(oldArr, newArr, hotelStartStrArr, 'hotelLinkMap' + cpuTypeSTr + '.xlsx', 'hotel'))
	#
	# onlineBookStartStrArr = ['TNOB']
	# resultStrArr.append(getTheReport(oldArr, newArr, onlineBookStartStrArr, 'onlineBookLinkMap' + cpuTypeSTr + '.xlsx', 'onlineBook'))
	#
	# wifiStartStrArr = ['TNWifi']
	# resultStrArr.append(getTheReport(oldArr, newArr, wifiStartStrArr, 'wifiLinkMap' + cpuTypeSTr + '.xlsx', 'wifi'))
	#
	# chatStartStrArr = ['TNChat']
	# resultStrArr.append(getTheReport(oldArr, newArr, chatStartStrArr, 'chatLinkMap' + cpuTypeSTr + '.xlsx', 'chat'))
	#
	# discoveryStartStrArr = ['TNCommunity', 'TNDiscovery','TNDC','TNTrip','TNCPersional','TNTravelTogether']  #发现
	# resultStrArr.append(getTheReport(oldArr, newArr, discoveryStartStrArr, 'discoveryLinkMap' + cpuTypeSTr + '.xlsx', 'discovery'))
	#
	# useCarStartStrArr = ['TNCar']  #用车
	# resultStrArr.append(getTheReport(oldArr, newArr, useCarStartStrArr, 'useCarLinkMap' + cpuTypeSTr + '.xlsx', 'useCar'))
	#
	# cruiseShipStartStrArr = ['TNCruiseShip']  #邮轮
	# resultStrArr.append(getTheReport(oldArr, newArr, cruiseShipStartStrArr, 'cruiseShipLinkMap' + cpuTypeSTr + '.xlsx', 'cruiseShip'))
	#
	# superStartStrArr = ['TNSuper']  #超级自由行
	# resultStrArr.append(getTheReport(oldArr, newArr, superStartStrArr, 'superLinkMap' + cpuTypeSTr + '.xlsx', 'super'))
	#
	# diyStrArr = ['TNBoss3DIY']  #BOSS3自由行.xlsx', 'total'
	# resultStrArr.append(getTheReport(oldArr, newArr, diyStrArr, 'boss3DiyLinkMap' + cpuTypeSTr + '.xlsx', 'diy'))
	#
	# payStrArr = ['TFPay']  #金融
	# resultStrArr.append(getTheReport(oldArr, newArr, payStrArr, 'payinkMap' + cpuTypeSTr + '.xlsx', 'pay'))

	f = open(os.path.split(os.path.realpath(__file__))[0] + '/LinkMapOutPut/' + cpuTypeSTr + '.txt','w')
    #f = open('/Users/server/Desktop/linkMapTest/LinkMapOutPut/' + cpuTypeSTr + '.txt','w')
	for resultStr in resultStrArr:
		print resultStr
		f.write(resultStr + '\n')
	f.close

	#shutil.move(newDir, oldDir) #将新的linkMap文件放入旧的中，替换掉（用来自动化执行）
	#print 'had moved New Dir 2 old Dir'
