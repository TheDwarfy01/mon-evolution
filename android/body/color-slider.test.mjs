import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('./measurements-ui.js',import.meta.url),'utf8');
const code=source.split('// COLOR_SLIDER_HELPERS_BEGIN')[1].split('// COLOR_SLIDER_HELPERS_END')[0];
const {gradientColor,gradientPosition,validColor}=vm.runInNewContext(code+'\n({gradientColor,gradientPosition,validColor})');
const palette=[['dark','#000000'],['mid','#804020'],['light','#FFFFFF']];
test('continuous interpolation preserves exact old palette colors',()=>{
 assert.equal(gradientColor(palette,0),'#000000');assert.equal(gradientColor(palette,100),'#804020');assert.equal(gradientColor(palette,200),'#FFFFFF');
 assert.equal(gradientColor(palette,50),'#402010');assert.equal(gradientPosition(palette,'#402010'),50);
 assert.equal(gradientPosition(palette,'#804020'),100);assert.ok(validColor('#123abc'));assert.ok(!validColor('red'));
});
test('boundaries and unknown saved shades remain safe',()=>{
 assert.equal(gradientColor(palette,-10),'#000000');assert.equal(gradientColor(palette,500),'#FFFFFF');
 assert.ok(gradientPosition(palette,'#123456')>=0);assert.ok(gradientPosition(palette,'#123456')<=200);
});