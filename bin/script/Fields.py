import uno
import string
import unohelper
from com.sun.star.task import XJobExecutor
from lib.gui import *
from lib.functions import *
from lib.error import ErrorDialog
import xmlrpclib

class Fields(unohelper.Base, XJobExecutor ):
    def __init__(self,sVariable="",sFields="",sDisplayName="",bFromModify=False):
        self.win = DBModalDialog(60, 50, 180, 225, "Field Builder")

        self.win.addFixedText("lblVariable", 27, 12, 60, 15, "Variable :")
        self.win.addComboBox("cmbVariable", 180-120-2, 10, 120, 15,True,
                            itemListenerProc=self.cmbVariable_selected)
        self.insVariable = self.win.getControl( "cmbVariable" )

        self.win.addFixedText("lblFields", 10, 32, 60, 15, "Variable Fields :")
        self.win.addComboListBox("lstFields", 180-120-2, 30, 120, 150, False,itemListenerProc=self.lstbox_selected)
        self.insField = self.win.getControl( "lstFields" )

        self.win.addFixedText("lblUName", 8, 187, 60, 15, "Displayed name :")
        self.win.addEdit("txtUName", 180-120-2, 185, 120, 15,)

        self.sObj=None
        self.win.addButton('btnOK',-5 ,-5,45,15,'Ok'
                     ,actionListenerProc = self.btnOkOrCancel_clicked )
        self.win.addButton('btnCancel',-5 - 45 - 5 ,-5,45,15,'Cancel'
                      ,actionListenerProc = self.btnOkOrCancel_clicked )
        self.aItemList=[]
        self.aComponentAdd=[]
        self.aObjectList=[]
        self.aListFields=[]
        EnumDocument(self.aItemList,self.aComponentAdd)
        desktop=getDesktop()
        doc =desktop.getCurrentComponent()
        docinfo=doc.getDocumentInfo()
        self.sMyHost= ""
        if not docinfo.getUserFieldValue(3) == "" and not docinfo.getUserFieldValue(0)=="":
            self.sMyHost= docinfo.getUserFieldValue(0)
            self.count=0
            oParEnum = doc.getTextFields().createEnumeration()
            while oParEnum.hasMoreElements():
                oPar = oParEnum.nextElement()
                if oPar.supportsService("com.sun.star.text.TextField.DropDown"):
                    self.count += 1
            getList(self.aObjectList, self.sMyHost,self.count)
            cursor = doc.getCurrentController().getViewCursor()
            text=cursor.getText()
            tcur=text.createTextCursorByRange(cursor)
            for j in range(self.aObjectList.__len__()):
                if self.aObjectList[j].__getslice__(0,self.aObjectList[j].find("(")) == "Objects":
                    self.insVariable.addItem(self.aObjectList[j],1)
            for i in range(self.aItemList.__len__()):
                if self.aComponentAdd[i]=="Document":
                    sLVal=self.aItemList[i].__getitem__(1).__getslice__(self.aItemList[i].__getitem__(1).find(",'")+2,self.aItemList[i].__getitem__(1).find("')"))
                    for j in range(self.aObjectList.__len__()):
                        if self.aObjectList[j].__getslice__(0,self.aObjectList[j].find("(")) == sLVal:
                            self.insVariable.addItem(self.aObjectList[j],1)
                if tcur.TextSection:
                    if self.aComponentAdd[i]== tcur.TextSection.Name:
                        sLVal=self.aItemList[i].__getitem__(1).__getslice__(self.aItemList[i].__getitem__(1).find(",'")+2,self.aItemList[i].__getitem__(1).find("')"))
                        for j in range(self.aObjectList.__len__()):
                            if self.aObjectList[j].__getslice__(0,self.aObjectList[j].find("(")) == sLVal:
                                self.insVariable.addItem(self.aObjectList[j],1)
                if tcur.TextTable:
                    if not self.aComponentAdd[i] == "Document" and self.aComponentAdd[i].__getslice__(self.aComponentAdd[i].rfind(".")+1,self.aComponentAdd[i].__len__())== tcur.TextTable.Name:
                        VariableScope(tcur,self.insVariable,self.aObjectList,self.aComponentAdd,self.aItemList,self.aComponentAdd[i])#self.aComponentAdd[i].__getslice__(self.aComponentAdd[i].rfind(".")+1,self.aComponentAdd[i].__len__())
            self.bModify=bFromModify
            if self.bModify==True:
                sItem=""
                i=0
                for i in range(self.aObjectList.__len__()):
                    if self.aObjectList[i].__getslice__(0,self.aObjectList[i].find("("))==sVariable:
                        sItem= self.aObjectList[i]
                        self.insVariable.setText(sItem)
                genTree(sItem.__getslice__(sItem.find("(")+1,sItem.find(")")),self.aListFields, self.insField,self.sMyHost,2,ending_excl=['one2many','many2one','many2many','reference'], recur=['many2one'])
                self.win.setEditText("txtUName",sDisplayName)
            self.win.doModalDialog()
        else:
            ErrorDialog("Please insert user define field Field-1 or Field-4","Just go to File->Properties->User Define \nField-1 Eg. http://localhost:8069 \nOR \nField-4 Eg. account.invoice")
            self.win.endExecute()

    def lstbox_selected(self,oItemEvent):
        try:
            sock = xmlrpclib.ServerProxy(self.sMyHost + '/xmlrpc/object')
            sItem=self.win.getComboBoxSelectedText("cmbVariable")
            sMain=self.aListFields[self.win.getListBoxSelectedItemPos("lstFields")]
            sObject=self.getRes(sock,sItem.__getslice__(sItem.find("(")+1,sItem.__len__()-1),sMain.__getslice__(1,sMain.__len__()))
            res = sock.execute('terp', 3, 'admin', sObject , 'read',[1])
            self.win.setEditText("txtUName",res[0][(sMain.__getslice__(sMain.rfind("/")+1,sMain.__len__()))])
        except:
            #import traceback;traceback.print_exc()
            self.win.setEditText("txtUName","Error(NULL Value)-Please Enter value")
    def getRes(self,sock ,sObject,sVar):
        res = sock.execute('terp', 3, 'admin', sObject , 'fields_get')
        key = res.keys()
        key.sort()
        if not sVar.find("/")==-1:
            myval=sVar.__getslice__(0,sVar.find("/"))
        else:
            myval=sVar
        for k in key:
            if k==myval:
                return sObject #res[myval]['relation']
            if (res[k]['type'] in ['many2one']) and k==myval:
                self.getRes(sock,res[myval]['relation'], sVar.__getslice__(sVar.find("/")+1,sVar.__len__()))
    def cmbVariable_selected(self,oItemEvent):
        if self.count > 0 :
            sock = xmlrpclib.ServerProxy(self.sMyHost + '/xmlrpc/object')
            desktop=getDesktop()
            doc =desktop.getCurrentComponent()
            docinfo=doc.getDocumentInfo()
            self.win.removeListBoxItems("lstFields", 0, self.win.getListBoxItemCount("lstFields"))
            self.aListFields=[]
            sItem=self.win.getComboBoxSelectedText("cmbVariable")
            genTree(sItem.__getslice__(sItem.find("(")+1,sItem.find(")")),self.aListFields, self.insField,self.sMyHost,2,ending_excl=['one2many','many2one','many2many','reference'], recur=['many2one'])

    def btnOkOrCancel_clicked( self, oActionEvent ):
        #Called when the OK or Cancel button is clicked.
        if oActionEvent.Source.getModel().Name == "btnOK":
            self.bOkay = True
            desktop=getDesktop()
            doc = desktop.getCurrentComponent()
            text = doc.Text
            cursor = doc.getCurrentController().getViewCursor()
            if self.win.getListBoxSelectedItem("lstFields") != "" and self.win.getEditText("txtUName") != "" and self.bModify==True :
                oCurObj=cursor.TextField
                sObjName=self.insVariable.getText()
                sObjName=sObjName.__getslice__(0,sObjName.find("("))
                sKey=u""+ self.win.getEditText("txtUName")
                sValue=u"[[ " + sObjName + self.aListFields[self.win.getListBoxSelectedItemPos("lstFields")].replace("/",".") + " ]]"
                oCurObj.Items = (sKey,sValue)
                oCurObj.update()
                self.win.endExecute()
            elif self.win.getListBoxSelectedItem("lstFields") != "" and self.win.getEditText("txtUName") != "" :
                sObjName=""
                oInputList = doc.createInstance("com.sun.star.text.TextField.DropDown")
                sObjName=self.win.getComboBoxSelectedText("cmbVariable")
                sObjName=sObjName.__getslice__(0,sObjName.find("("))
                if cursor.TextTable==None:
                    sKey=u""+ self.win.getEditText("txtUName")
                    sValue=u"[[ " + sObjName + self.aListFields[self.win.getListBoxSelectedItemPos("lstFields")].replace("/",".") + " ]]"
                    oInputList.Items = (sKey,sValue)
                    text.insertTextContent(cursor,oInputList,False)
                else:
                    oTable = cursor.TextTable
                    oCurCell = cursor.Cell
                    tableText = oTable.getCellByName( oCurCell.CellName )
                    sKey=u""+ self.win.getEditText("txtUName")
                    sValue=u"[[ " + sObjName + self.aListFields[self.win.getListBoxSelectedItemPos("lstFields")].replace("/",".") + " ]]"
                    oInputList.Items = (sKey,sValue)
                    tableText.insertTextContent(cursor,oInputList,False)
                self.win.endExecute()
            else:
                    ErrorDialog("Please Fill appropriate data in Name field \nor select perticular value from the list of fields")
        elif oActionEvent.Source.getModel().Name == "btnCancel":
            self.win.endExecute()

if __name__=="__main__":
    Fields()
#else:
#    g_ImplementationHelper.addImplementation( \
#        Fields,
#        "org.openoffice.tiny.report.fields",
#        ("com.sun.star.task.Job",),)


