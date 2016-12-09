#!/usr/bin/python
#coding:utf-8
#这个脚本是为了统计 分析出来的linkMap的文件大小 的总和
#
import os,sys,shutil
import xlsxwriter   # xlsxwriter 用户生成xlsx文件
from string import Template


class sizeFile:  
	#定义基本属性  
	moduleName = ''  
	lastSize = 0 
	currentSize = 0 
	#定义构造方法  
	def __init__(self,n,s,d):  
		self.moduleName = n  
		self.lastSize = s 
		self.currentSize = d

	def show(self):  
		print("moduleName: %s lastSize: %d currentSize: %d" %(self.moduleName,self.lastSize,self.currentSize)) 


class sizeMapReader(object):

	def __init__(self, sizemapdir):
		super(sizeMapReader, self).__init__()
		self.sizemapdir=sizemapdir

	#read objs From linkmapdir
	def readObjectFrom(self):
		f=open(self.sizemapdir, "r")
		arr = []
		for line in f:
			if line.find("moduleName:")!=-1 and line.find("lastSize:")!=-1 and line.find("currentSize:")!=-1:
				tempStr = line.replace('moduleName:',' ')
				tempStr = tempStr.replace('lastSize:',' ')
				tempStr = tempStr.replace('currentSize:',' ')
				print tempStr
				objInfo=tempStr.split(',')
				if len(objInfo)==3:
					singleFile = sizeFile(objInfo[0],int(objInfo[1]),int(objInfo[2]))
					arr.append(singleFile)
		f.close
		return arr

def formatSize(kybeSize):
	return float('%.2f'%(float(kybeSize) / 1024))

if __name__=='__main__':
	if len(sys.argv) < 2:
		print 'Not enough Params'
		sys.exit(0)

	oldDir = sys.argv[1]
	newDir = sys.argv[2]

	if oldDir.count('arm64') > 0 and newDir.count('-armv7') > 0:
		arm64Dir = oldDir
		armv7Dir = newDir
	elif newDir.count('arm64') > 0 and oldDir.count('-armv7') > 0:
		arm64Dir = newDir
		armv7Dir = oldDir		
	else:
		print 'Params error'
		sys.exit(0)
	
	arm64SizeReader = sizeMapReader(arm64Dir)
	armv7SizeReader = sizeMapReader(armv7Dir)
	arm64Arr = arm64SizeReader.readObjectFrom()
	armv7Arr = armv7SizeReader.readObjectFrom()

	dirName = os.path.split(os.path.realpath(__file__))[0] + '/LinkMapOutPut/' + 'linkMapSize.xlsx'
	workbook = xlsxwriter.Workbook(dirName)
	worksheet = workbook.add_worksheet()

	worksheet.set_column('A:A',13)    #设定列的宽度为60像素
	worksheet.set_column('B:B',13)
	worksheet.set_column('C:C',13)
	worksheet.set_column('D:D',13)
	worksheet.set_column('E:E',13)

	currentRow = 0
	worksheet.write(currentRow, 0, 'Name')
	worksheet.write(currentRow, 1, 'lastTotalSize')
	worksheet.write(currentRow, 2, 'currentTotalSize')
	worksheet.write(currentRow, 3, 'change')

	format_title_add = workbook.add_format()    #定义format_title格式对象
	format_title_add.set_border(1)   #定义format_title对象单元格边框加粗(1像素)的格式
	#format_title_add.set_bg_color('#ef7175')   #定义format_title对象单元格背景颜色为'#cccccc'的格式

	for  obj64 in arm64Arr :
		obj64.show()
		for  objv7 in armv7Arr :
			if objv7.moduleName == obj64.moduleName:
				currentRow = currentRow + 1
				worksheet.write(currentRow, 0, obj64.moduleName, format_title_add)
				worksheet.write_number(currentRow, 1, formatSize(obj64.lastSize + objv7.lastSize), format_title_add)
				worksheet.write_number(currentRow, 2, formatSize(obj64.currentSize + objv7.currentSize), format_title_add)
				worksheet.write_number(currentRow, 3, formatSize(int(obj64.currentSize + objv7.currentSize) - int(obj64.lastSize + objv7.lastSize)), format_title_add)
				print("moduleName: %s lastSize: %d currentSize: %d hasChanged: %d ." %(obj64.moduleName, formatSize(obj64.lastSize + objv7.lastSize), formatSize(obj64.currentSize + objv7.currentSize), formatSize(int(obj64.currentSize + objv7.currentSize) - int(obj64.lastSize + objv7.lastSize)) )) 
	workbook.close()



