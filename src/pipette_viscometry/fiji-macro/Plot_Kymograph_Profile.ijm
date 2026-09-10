currentSlice = getSliceNumber();
//makeLine(262, 293, 262, 125);
Dialog.create("Plot Right-Most Dark Peak");
Dialog.addNumber("First frame", currentSlice);
Dialog.addNumber("Last frame", nSlices);
Dialog.addMessage("The threshold is the percentage of the average\nof the right half profile in the first frame");
Dialog.addNumber("Threshold (in percent)", 95);
Dialog.addCheckbox("Show_kymograph", !false);
Dialog.show();

beginFrame = Dialog.getNumber();
endFrame = Dialog.getNumber();
if (beginFrame == endFrame)
	exit("Need more than one frame for the analysis");
thresholdPercentage = Dialog.getNumber();
showKymograph = Dialog.getCheckbox();

function getLineLength() {
	getVoxelSize(width, height, depth, unit);
	getSelectionCoordinates(x, y);
	dx = x[x.length - 1] - x[0];
	dy = y[y.length - 1] - y[0];
	return sqrt(dx * dx * width * width + dy * dy * height * height);
}

function getLineLengthUnit() {
	getVoxelSize(width, height, depth, unit);
	return unit;
}

function getAverage(array, begin, end) {
	result = 0;
	for (i = begin; i < end; i++)
		result += array[i];
	return result / (end - begin);
}

function getBaseline() {
	profile = getProfile();
	return getAverage(profile, profile.length / 2, profile.length);
}

function parseSeconds(string) {
	if (endsWith(string, " s"))
		return parseFloat(substring(string, 0, lengthOf(string) - 2));
	return 0;
}

function findRightMostDarkPeak(array, threshold) {
	for (i = array.length - 1; i >= 0; i--)
		if (array[i] < threshold)
			return i;
	return -1;
}

setBatchMode(true);

// First, get the baseline by looking at the right half in the
// initial frame. The threshold is set to 80% of that.

threshold = getBaseline() * thresholdPercentage / 100.0;

lineLength = getLineLength();
lengthUnit = getLineLengthUnit();
setSlice(beginFrame);
beginTime = parseSeconds(getInfo("slice.label"));
if (beginTime > 0) {
	setSlice(endFrame);
	totalTime = parseSeconds(getInfo("slice.label")) - beginTime;
	timeUnit = "second";
}
else {
	totalTime = endFrame + 1 - beginFrame;
	timeUnit = "frame";
}

xValues = newArray(endFrame + 1 - beginFrame);
yValues = newArray(xValues.length);

for (i = beginFrame; i <= endFrame; i++) {
	setSlice(i);
	profile = getProfile();
	if (i == beginFrame)
		kymograph = newArray(profile.length * xValues.length);

	offset = i - beginFrame;
	xValues[offset] = totalTime * offset / xValues.length;
	yValues[offset] = findRightMostDarkPeak(profile, threshold) * lineLength / profile.length;
	for (j = 0; j < profile.length; j++)
		kymograph[offset + (profile.length - 1 - j) * xValues.length]
			= profile[j];
}
setSlice(currentSlice);
setBatchMode(false);

if (showKymograph) {
	width = xValues.length;
	height = kymograph.length / width;
	newImage("Kymograph", "32-bit", width, height, 1);
	setVoxelSize(totalTime / width, lineLength / height, 1, timeUnit + "/" + lengthUnit);
	setMinAndMax(0, 255);
	setBatchMode(true);
	for (i = 0; i < width; i++)
		for (j = 0; j < height; j++)
			setPixel(i, j, kymograph[i + j * width]);
	setBatchMode(false);
}

Plot.create("Right-most dark peaks over time", timeUnit, lengthUnit, xValues, yValues);
Plot.show();
