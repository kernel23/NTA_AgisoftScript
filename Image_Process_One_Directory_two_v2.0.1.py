import Metashape
import os, sys, time
import glob
import shutil

# Checking compatibility
compatible_major_version = "2.1"
found_major_version = ".".join(Metashape.app.version.split('.')[:2])
if found_major_version != compatible_major_version:
    raise Exception("Incompatible Metashape version: {} != {}".format(found_major_version, compatible_major_version))

# 1. Ask the user to select the folders via GUI pop-ups
root_dir = Metashape.app.getExistingDirectory("Select the ROOT directory containing your image folders:")
if not root_dir:
    raise Exception("Script aborted: No root directory selected.")

output_dir = Metashape.app.getExistingDirectory("Select the OUTPUT directory for your TIFs and KMZs:")
if not output_dir:
    raise Exception("Script aborted: No output directory selected.")

mov_dir = Metashape.app.getExistingDirectory("Select the directory to MOVE finished image folders to:")
if not mov_dir:
    raise Exception("Script aborted: No move directory selected.")

# 2. Safely create export paths
output_TIF = os.path.join(output_dir, 'Output_TIF')
output_KMZ = os.path.join(output_dir, 'Output_KMZ')
output_project_folder = os.path.join(root_dir, 'output_project_files')

# Create the output directories if they don't already exist
os.makedirs(output_TIF, exist_ok=True)
os.makedirs(output_KMZ, exist_ok=True)
os.makedirs(output_project_folder, exist_ok=True)

dir_name = ''
prev_doc = ''
dirs_with_jpg = []
processed_count = 0  # <--- NEW: Initialize a counter to track finished folders

# 3. Walk through each directory looking for JPGs (case-insensitive)
for root, dirs, files in os.walk(root_dir):
    if any(file.upper().endswith(".JPG") for file in files):
        dirs_with_jpg.append(root)

# 4. Process each folder
for dir_with_jpg in dirs_with_jpg:
    dir_name = os.path.basename(dir_with_jpg)
    doc = Metashape.Document()  # new Document
    path_project = os.path.join(output_project_folder, dir_name + '_project.psx')
    
    doc.save(path_project) 
    
    # Delete previous project folder to save space
    try:
        if prev_doc != '':
            shutil.rmtree(prev_doc)
            print('Previous project folder deleted. Proceeding to next folder')
    except:
        print("Can't Delete the previous file")
    
    chunk = doc.addChunk() 

    # Load photos (case-insensitive check)
    photos = [os.path.join(dir_with_jpg, file) for file in os.listdir(dir_with_jpg) if file.upper().endswith('.JPG')]
    chunk.addPhotos(photos)  
    doc.save()  

    print(str(len(chunk.cameras)) + " images loaded for " + dir_name)  

    chunk.matchPhotos(downscale=2, keypoint_limit=40000, tiepoint_limit=4000, generic_preselection=True, reference_preselection=True)  
    doc.save()

    chunk.alignCameras()  
    doc.save()
    
    has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation
    
    if has_transform:        
        chunk.buildDem(source_data=Metashape.TiePointsData)
        doc.save()
        
        chunk.buildOrthomosaic(surface_data=Metashape.ElevationData) 
        doc.save()

    # 5. Export results
    if chunk.orthomosaic:
        orthomosaic_path = os.path.join(output_TIF, dir_name + '_ortho.tif')
        chunk.exportRaster(orthomosaic_path, source_data=Metashape.OrthomosaicData, resolution=0.05)
	
        kmz_path = os.path.join(output_KMZ, dir_name + '_ortho.kmz')
        chunk.exportRaster(kmz_path, format=Metashape.RasterFormatKMZ, description='Generated through automated python script')
        
        # Move the finished directory
        shutil.move(dir_with_jpg, mov_dir) 
        
        # Remove the .files folder associated with the Metashape project
        prev_doc = os.path.splitext(path_project)[0] + '.files'
        
        # <--- NEW: Increase the counter by 1 since this folder successfully finished
        processed_count += 1 

print('Processing finished')

# <--- NEW: Trigger the pop-up dialog box when the loop is entirely done
Metashape.app.messageBox("Processing Complete!\n\nSuccessfully processed " + str(processed_count) + " folder(s).")