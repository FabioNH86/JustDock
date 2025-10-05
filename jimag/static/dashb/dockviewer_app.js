import { DockingViewer } from 'molstar/lib/apps/docking-viewer';
const djangovars = document.currentScript.dataset;
const conformers = djangovars.conformers;
const receptor = djangovars.receptor;
/*var palette = [0x992211, 0xDDDDDD, 0x33DD22, 0x1133EE];*/
var palette = [0xaa7574];
console.log(conformers, receptor);
DockingViewer.create('app', palette, {
    layoutIsExpanded: false,
    layoutShowControls: false,
    layoutShowRemoteState: false,
    layoutShowSequence: true,
    layoutShowLog: false,
    layoutShowLeftPanel: true,

    viewportShowExpand: true,
    viewportShowControls: true,
    viewportShowSelectionMode: true,
    viewportShowAnimation: false,

    pdbProvider: 'rcsb',
    emdbProvider: 'rcsb',
}).then(viewer => {
    viewer.loadStructuresFromUrlsAndMerge([
		{url: conformers, format: 'pdbqt'},
		{url: receptor, format: 'pdbqt'}
	]);
});
