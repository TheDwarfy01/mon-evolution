import test from 'node:test';
import assert from 'node:assert/strict';
import {estimateVisualMeasurements} from './visual-defaults.mjs';
import {readBellyVisualCalibration,calibrateBellyVisualEquivalent,saveBellyVisualCalibration,clearBellyVisualCalibration} from './visual-calibration.mjs';
function store(){const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)};}
test('user may calibrate a 95.4 cm aesthetic estimate to approximately 160 cm',()=>{
 const s=store();
 assert.equal(saveBellyVisualCalibration('adult',95.4,160,s),true);
 const factor=readBellyVisualCalibration('adult',s);
 assert.ok(factor>1.6&&factor<1.7);
 assert.equal(calibrateBellyVisualEquivalent(95.4,factor),160);
 assert.equal(readBellyVisualCalibration('unrelated',s),1);
});
test('equivalence follows subsequent changes in weight rather than freezing 160 cm',()=>{
 const s=store(),p={height:170,weight:88,age:39,sex:'male',child:false};
 const first=estimateVisualMeasurements(p).belly;
 const second=estimateVisualMeasurements({...p,weight:100}).belly;
 assert.ok(second>first);
 assert.equal(saveBellyVisualCalibration('adult',first,160,s),true);
 const ratio=readBellyVisualCalibration('adult',s);
 assert.equal(calibrateBellyVisualEquivalent(first,ratio),160);
 assert.ok(calibrateBellyVisualEquivalent(second,ratio)>160);
});
test('calibration is visual-only, reversible and cannot be treated as a measurement',()=>{
 const s=store(),p={height:170,weight:88,age:39,sex:'male',child:false};
 const original=estimateVisualMeasurements(p);
 const before=JSON.stringify(original);
 assert.equal(saveBellyVisualCalibration('adult',original.belly,160,s),true);
 assert.equal(JSON.stringify(original),before,'measurements or estimate object must not be mutated');
 assert.ok(clearBellyVisualCalibration('adult',s));
 assert.equal(readBellyVisualCalibration('adult',s),1);
 assert.equal(calibrateBellyVisualEquivalent(original.belly,1),original.belly);
});
test('invalid values, nonfinite inputs, excessive ratios and malformed storage fail safe',()=>{
 const s=store();
 assert.equal(saveBellyVisualCalibration('adult',95.4,250,s),false);
 assert.equal(saveBellyVisualCalibration('adult',95.4,NaN,s),false);
 assert.equal(saveBellyVisualCalibration('',95.4,160,s),false);
 assert.equal(calibrateBellyVisualEquivalent(NaN,1),null);
 assert.equal(readBellyVisualCalibration('',s),1);
});
