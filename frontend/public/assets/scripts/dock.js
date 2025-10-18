"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
//import React, { useState } from 'react';
//import ReactDOM from 'react-dom';
var React = require("react");
var ReactDOM = require("react-dom");
var spec_1 = require("molstar/lib/mol-plugin-ui/spec");
var index_1 = require("molstar/lib/mol-plugin-ui/index");
var config_1 = require("molstar/lib/mol-plugin/config");
var structure_1 = require("molstar/lib/mol-model/structure");
var MySpec = __assign(__assign({}, (0, spec_1.DefaultPluginUISpec)()), { config: [
        [config_1.PluginConfig.VolumeStreaming.Enabled, false],
        [config_1.PluginConfig.Viewport.ShowControls, false],
        [config_1.PluginConfig.Viewport.ShowSelectionMode, false],
        [config_1.PluginConfig.Viewport.ShowExpand, false],
        [config_1.PluginConfig.Viewport.ShowSettings, false],
        [config_1.PluginConfig.Viewport.ShowTrajectoryControls, false]
    ], layout: {
        initial: {
            regionState: {
                bottom: "hidden",
                top: "hidden",
                left: "hidden",
                right: "hidden",
            },
        },
    } });
var MyComponent = function () {
    var _a = React.useState([]), selected = _a[0], setSelected = _a[1];
    React.useEffect(function () {
        function initializePlugin() {
            return __awaiter(this, void 0, void 0, function () {
                var parent, plugin, data, trajectory;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            parent = document.getElementById('app2');
                            if (!parent)
                                return [2 /*return*/];
                            return [4 /*yield*/, (0, index_1.createPluginUI)(parent, MySpec)];
                        case 1:
                            plugin = _a.sent();
                            return [4 /*yield*/, plugin.builders.data.download({ url: 'https://files.rcsb.org/download/1a3n.pdb' }, { state: { isGhost: true } })];
                        case 2:
                            data = _a.sent();
                            return [4 /*yield*/, plugin.builders.structure.parseTrajectory(data, 'pdb')];
                        case 3:
                            trajectory = _a.sent();
                            return [4 /*yield*/, plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default')];
                        case 4:
                            _a.sent();
                            plugin.managers.interactivity.setProps({ granularity: 'chain' });
                            plugin.selectionMode = true;
                            plugin.behaviors.interaction.click.subscribe(function (event) {
                                var selections = Array.from(plugin.managers.structure.selection.entries.values());
                                //console.log("selections: ", selections);
                                // This bit can be customized to record any piece information you want
                                var localSelected = [];
                                for (var _i = 0, selections_1 = selections; _i < selections_1.length; _i++) {
                                    var structure = selections_1[_i].structure;
                                    //console.log("structure: ", structure);
                                    if (!structure)
                                        continue;
                                    structure_1.Structure.eachAtomicHierarchyElement(structure, {
                                        chain: function (loc) {
                                            var chainid = structure_1.StructureProperties.chain.auth_asym_id(loc);
                                            localSelected.push({ chainid: chainid });
                                        },
                                    });
                                }
                                setSelected(localSelected);
                                var chainString = localSelected.map(function (item) { return item.chainid; }).join(',');
                                console.log(chainString);
                                var stringDiv = document.getElementById('chainstring');
                                stringDiv.innerHTML = chainString;
                            });
                            return [2 /*return*/];
                    }
                });
            });
        }
        initializePlugin();
        return function () {
            //cleanup
        };
    }, []);
    return null;
};
ReactDOM.render(React.createElement(MyComponent), document.getElementById('chainsviewer'));