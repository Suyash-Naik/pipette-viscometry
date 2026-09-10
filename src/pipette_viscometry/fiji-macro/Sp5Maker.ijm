// written 03/06/2020SN
// save the files as a Experiment.lif files with 3 channels and multiple images
dir=getDirectory("Choose a Directory");
//open(dir+"Project.lif");
GreenFlour="TgGAPDHGFP";
RedFlour="TgUtrmCherry";
Control="ControlInjected";
Treatment="KA";

//Making the file folder.....
//setBatchMode(True);
list = getList("image.titles");
for (i=0; i<list.length; i++){

        selectWindow(list[i]);
		ImageTitle=getTitle();
		lenTit=lengthOf(ImageTitle);
		positionName="Pos0"+substring(ImageTitle, lenTit-2,lenTit);
		//chaneg the substring parameters
		File.makeDirectory(dir+"/"+positionName);
		dir2=dir+"/"+positionName+"/";

		//rotation
		//run("Rotate 90 Degrees Right");
		//run("Rotate... ", "angle=-64 grid=11 interpolation=Bilinear stack");

//For single color images skip this section of the loop
		run("Split Channels");
// opens the files as 3 separate images based on channels
//Green FLour FullStack and Max proj save
		selectWindow("C1-"+ImageTitle);
		//open("B:/home/PHD_data/Imaging_et_analysis/Fijiscripts/LUTs/HotGreen.lut");
		FileC1="FullStack_"+GreenFlour+"_"+positionName+".ome.tiff";
		saveAs("Tiff", dir2+FileC1);
		//run("OME-TIFF...", "save="+FileC1+" write_each_channel use export compression=Uncompressed");
		run("Z Project...", "projection=[Max Intensity] all");
		selectWindow("MAX_"+FileC1);
		MaxFileC1="MAX_"+GreenFlour+"_"+positionName+".tif";
		saveAs("Tiff", dir2+MaxFileC1);
//		close(FileC1);
		close(MaxFileC1);
//RedFlour fullStack and Max proj save
		selectWindow("C2-"+ImageTitle);
		run("Red Hot");
		FileC2="FullStack_"+RedFlour+"_"+positionName+".tif";
		saveAs("Tiff", dir2+FileC2);
		run("Z Project...", "projection=[Max Intensity] all");
		selectWindow("MAX_"+FileC2);
		MaxFileC2="MAX_"+RedFlour+"_"+positionName+".tif";
		saveAs("Tiff", dir2+MaxFileC2);
//		close(FileC2);
		close(MaxFileC2);
//DIC image single frame save
		selectWindow("C3-"+ImageTitle);
//		run("Duplicate...", "duplicate slices=16");
		//MaxFileDIC="DICMAX-"+positionName+".tif";
		saveAs("Tiff", dir2+"DIC_"+positionName+".tif");
//		close(MaxFileDIC);
}
run("Collect Garbage");