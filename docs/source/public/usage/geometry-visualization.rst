Visualize 3D geometry from IDF
------------------------------

If you get warnings in the EnergyPlus error file regarding the geometry or you want to check the generated 3D geometry
for another reason it is helpful to visualize the geometry.

There are a few ways you can do that:

- For programming language R there is a package called "eplusr" with which you can read your IDF file and visualize the geometry
  There is an example R-script including installation instructions in the cesar-p-usage-examples repository under pre_or_postprocessing_scripts.
- The python library geomeppy can create a 3D obj file from an IDF, which you can view in a online 3D viewer. 
   There is an example the cesar-p-usage-examples repository under pre_or_postprocessing_scripts.
   With this method, the buildings get visualized upside down sometimes, so that process might not be too reliable
- A IDF Viewer written in Java: https://bitbucket.org/empa_lbst/idf-viewer
- with the IDF Viewer shipped with Energy Plus there should be an option to visualize the IDF as well (but I havent searched for it)