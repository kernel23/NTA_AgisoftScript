#Hope this loops in your project folder
import Metashape
import os, sys, time
import glob
import shutil

# Checking compatibility
compatible_major_version = "2.1"
found_major_version = ".".join(Metashape.app.version.split('.')[:2])
if found_major_version != compatible_major_version:
    raise Exception("Incompatible Metashape version: {} != {}".format(found_major_version, compatible_major_version))
	
if len(sys.argv) < 4:
    print("Usage: general_workflow.py <image_folder> <Output_folder>")
    raise Exception("Invalid script arguments")
	
root_dir = sys.argv[1] # 
output_dir = sys.argv[2]
mov_dir = sys.argv[3]
output_TIF = output_dir + '_TIF'
output_KMZ = output_dir + '_KMZ'
output_project_folder = root_dir + 'output_project_files'
dir_name = ''
prev_doc = ''
# Initialize an empty list to store directories
dirs_with_jpg = []

# Walk through each directory in the root directory
for root, dirs, files in os.walk(root_dir):
    # Check if any file in the directory ends with .JPG
    if any(file.endswith(".JPG") for file in files):
        # If yes, add the directory to the list
        dirs_with_jpg.append(root)

for dir_with_jpg in dirs_with_jpg:
    dir_name = os.path.basename(dir_with_jpg)
    doc = Metashape.Document()  # new Document
    path_project = os.path.join(output_project_folder+dir_name, dir_name + 'project.psx')
    
    doc.save(path_project)  # Saves the new Document, Usually the name of project is the name of the photos folder
    try:
        if prev_doc != '':
            shutil.rmtree(prev_doc)
            print('Previous project folder deleted. Proceeding to next folder')
    except :
        print("Can't Delete the file");
    
    chunk = doc.addChunk()  # Creates new Chunk

    photos = [os.path.join(dir_with_jpg, file) for file in os.listdir(dir_with_jpg) if file.endswith('.JPG')]
    chunk.addPhotos(photos)  # adds photos to the chunk
    doc.save()  # Save project

    print(str(len(chunk.cameras)) + " images loaded")  # Displays the number of images loaded

    chunk.matchPhotos(downscale = 2, keypoint_limit=40000, tiepoint_limit=4000, generic_preselection=True, reference_preselection=True)  # Align the photos
    doc.save()

    chunk.alignCameras()  # aligns the cameras
    doc.save()
    
    has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation
    
    if has_transform:        
        chunk.buildDem(source_data=Metashape.TiePointsData)
        doc.save()
        
        chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)  # Builds the Orthomosaic
        doc.save()

        # export results
        # Get the directory name
    
    # export results
    if chunk.orthomosaic:
        orthomosaic_path = os.path.join(output_TIF, dir_name + '_ortho.tif')
        chunk.exportRaster(orthomosaic_path, source_data=Metashape.OrthomosaicData, resolution =0.05 )
	
        kmz_path = os.path.join(output_KMZ, dir_name + '_ortho.kmz')
        chunk.exportRaster(kmz_path, format = Metashape.RasterFormatKMZ,  description = 'Generated through automated python script')
        # Delete the directory folder of the finished orthomosaic
        shutil.move(dir_with_jpg, mov_dir) 
        #shutil.rmtree(dir_with_jpg)
        prev_doc = output_project_folder+dir_name
              

print('Processing finished')
