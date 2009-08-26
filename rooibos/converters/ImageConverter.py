import uno
import unohelper
from com.sun.star.beans import PropertyValue

DEFAULT_OPENOFFICE_PORT = "8100"

# The Desktop object.
# It is cached in a global variable.
oDesktop = False

# The ServiceManager of the running OOo.
# It is cached in a global variable.
oServiceManager = False
	
# The CoreReflection object.
# It is cached in a global variable.
oCoreReflection = False

class ImageConversionException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class ImageConverter:

	def getServiceManager( self, cHost="localhost", cPort=DEFAULT_OPENOFFICE_PORT ):
	    """Get the ServiceManager from the running OpenOffice.org.
	        Then retain it in the global variable oServiceManager for future use.
	    """
	    global oServiceManager
	    if not oServiceManager:
	        # Get the uno component context from the PyUNO runtime
	        oLocalContext = uno.getComponentContext()
	       
	        # Create the UnoUrlResolver on the Python side.
	        oLocalResolver = oLocalContext.ServiceManager.createInstanceWithContext(
	                                    "com.sun.star.bridge.UnoUrlResolver", oLocalContext )
	       
	        # Connect to the running OpenOffice.org and get its context.
	        oContext = oLocalResolver.resolve( "uno:socket,host=" + cHost + ",port=" + cPort + ";urp;StarOffice.ComponentContext" )
	       
	        # Get the ServiceManager object
	        oServiceManager = oContext.ServiceManager
	    return oServiceManager
	
	# This is the same as ServiceManager.createInstance( ... )
	def createUnoService( self,cClass ):
	    """A handy way to create a global objects within the running OOo.
	    """
	    oServiceManager = self.getServiceManager()
	    oObj = oServiceManager.createInstance( cClass )
	    return oObj
	
	def getDesktop(self):
	    """An easy way to obtain the Desktop object from a running OOo.
	    """
	    global oDesktop
	    if not oDesktop:
	        oDesktop = self.createUnoService( "com.sun.star.frame.Desktop" )
	    return oDesktop
	
	def getCoreReflection(self):
	    global oCoreReflection
	    if not oCoreReflection:
	        oCoreReflection = self.createUnoService( "com.sun.star.reflection.CoreReflection" )
	    return oCoreReflection
	
	def createUnoStruct( self, cTypeName ):
	    """Create a UNO struct and return it.
	    """
	    oCoreReflection = self.getCoreReflection()
	
	    # Get the IDL class for the type name
	    oXIdlClass = oCoreReflection.forName( cTypeName )
	
	    # Create the struct.
	    oReturnValue, oStruct = oXIdlClass.createObject( None )
	
	    return oStruct
	
	#------------------------------------------------------------
	#   Shape functions
	#------------------------------------------------------------
	
	def makePoint( self, nX, nY ):
	    """Create a com.sun.star.awt.Point struct."""
	    oPoint = self.createUnoStruct( "com.sun.star.awt.Point" )
	    oPoint.X = nX
	    oPoint.Y = nY
	    return oPoint
	
	def makeSize( self, nWidth, nHeight ):
	    """Create a com.sun.star.awt.Size struct."""
	    oSize = self.createUnoStruct( "com.sun.star.awt.Size" )
	    oSize.Width = nWidth
	    oSize.Height = nHeight
	    return oSize

	def loadGraphicIntoDocument( self, oDoc, cUrl, cInternalName ):
	   """ Get the BitmapTable from this drawing document.
	   It is a service that maintains a list of bitmaps that are internal
	   to the document.
	   """
	   oBitmaps = oDoc.createInstance( "com.sun.star.drawing.BitmapTable" )
	   
	   #Add an external graphic to the BitmapTable of this document.
	   oBitmaps.insertByName( cInternalName, cUrl )
	   
	   #Now ask for it back.
	   #What we get back is an different Url that points to a graphic
	   #which is inside this document, and remains with the document.
	   cNewUrl = oBitmaps.getByName( cInternalName )
	   
	   return cNewUrl 
	
	def makeGraphicObjectShape( self, oDoc, oPosition, oSize ):
		oShape = oDoc.createInstance( "com.sun.star.drawing.GraphicObjectShape" )
		oShape.Position = oPosition
		oShape.Size = oSize
		return oShape 
	
	def createPresentation(self,destUrl,images):   
		# Create a new drawing.
		oDrawDoc = self.getDesktop().loadComponentFromURL( "private:factory/simpress", "_blank", 0, () )
		
		count = 0
		
		for image in images:
			image = unohelper.systemPathToFileUrl(image)
			print image
			# If not the first page create a new page
			if count > 0:
				oDrawPages = oDrawDoc.getDrawPages().insertNewByIndex(count);
	
			# Get its first page.
			oDrawPage = oDrawDoc.getDrawPages().getByIndex( count )
			
			#Convert the URL into an internal URL within the document.
			#If you comment out this line, then the shape that is created from the url
			#will refer to the external graphic, which must always be present.
			cUrl = self.loadGraphicIntoDocument( oDrawDoc, image, str(count) )
			#Now the URL points to a graphic *inside* of the document's Zip file, rather than an external url.
			
			#Create a GraphicObjectShape.
			oShape = self.makeGraphicObjectShape( oDrawDoc, self.makePoint( 0, 0 ), self.makeSize( 28000, 21000 ) )
			#Add it to the drawing page.
			oDrawPage.add( oShape )
			#Set its URL to a particular graphic.
			oShape.GraphicURL = image
			count = count+1
	
		#oDrawDoc.storeAsURL(destUrl,())
	
		property = (
		    PropertyValue( "FilterName" , 0, "MS PowerPoint 97" , 0 ),
		)
		oDrawDoc.storeToURL(destUrl,property)
		#oDrawDoc.dispose()

if __name__ == "__main__":
    from sys import argv, exit
    import time
    
    if len(argv) < 3:
        print "USAGE: python %s <ppt-path> <images> " % argv[0]
        exit(255)

    try:
		imageConverter = ImageConverter()
		ppt_file = unohelper.systemPathToFileUrl(argv.pop(1))
		argv.pop(0)
		imageConverter.createPresentation(ppt_file, argv)
		# TODO: Delete Temp File

    except ImageConversionException, exception:
        print "ERROR!" + str(exception)
        exit(1)