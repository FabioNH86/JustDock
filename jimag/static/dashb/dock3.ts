import { DefaultPluginUISpec, PluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui';
import { renderReact18 } from 'molstar/lib/mol-plugin-ui/react18';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { Asset } from 'molstar/lib/mol-util/assets';

const djangovars = document.currentScript.dataset;
const conformers = djangovars.conformers;
const receptor = djangovars.receptor;

const MySpec: PluginUISpec = {
    ...DefaultPluginUISpec(),
    config: [
        [PluginConfig.VolumeStreaming.Enabled, false],
        [PluginConfig.Viewport.ShowControls, true],
        [PluginConfig.Viewport.ShowSelectionMode, false],
        [PluginConfig.Viewport.ShowExpand, true],
        [PluginConfig.Viewport.ShowSettings, true],
        [PluginConfig.Viewport.ShowTrajectoryControls, false]
    ],
    layout: {
	initial: { //more in viewer/app.ts
	    isExpanded: false,
	    regionState: {
		top: "hidden",
		left: "full",
		right: "full",
		bottom: "hidden",
	    },
	},
    },
}

async function createPlugin(parent: HTMLElement) {
    const plugin = await createPluginUI({
      target: parent,
      spec: MySpec,
      render: renderReact18
    });

    //const rawdata = await plugin.builders.data.rawData({ data: receptor });
    const receptorData = await plugin.builders.data.download({
        url: Asset.Url(receptor),
        isBinary: false
    }, {state: {isGhost: true}});
    const receptorTrajectory = await plugin.builders.structure.parseTrajectory(receptorData, 'pdbqt');
    await plugin.builders.structure.hierarchy.applyPreset(receptorTrajectory, 'default');
    //const model = await plugin.builders.structure.createModel(trajectory);
    const conformersData = await plugin.builders.data.download({
        url: Asset.Url(conformers),
        isBinary: false
    }, {state: {isGhost: true}});
    const conformersTrajectory = await plugin.builders.structure.parseTrajectory(conformersData, 'pdbqt');
    await plugin.builders.structure.hierarchy.applyPreset(conformersTrajectory, 'default');

    return plugin;
}

createPlugin(document.getElementById('pockets-viewer')!); // app is a <div> element with position: relative
