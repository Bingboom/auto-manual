import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const template = readFileSync(new URL('../tools/rtd_portal_assets/moved_page.html', import.meta.url), 'utf8');
const script = template.match(/<script>([\s\S]*?)<\/script>/)[1];

for (const path of ['/en/latest/workspace/data/', '/en/latest/workspace/data/index.html']) {
  for (const query of ['', '?region=EU&model=JE-1000F',
    '?model=JE%2B1000F&region=EU&region=US&note=%E4%B8%AD%E6%96%87+%26%23',
    '?next=https%3A%2F%2Fexample.invalid%2F&region=EU']) {
    test(`old URL preserves its complete query: ${path}${query}`, () => {
      const current = new URL(`https://docs.example.test${path}${query}#assets`);
      const link = {href: new URL('../deliverables/index.html#statistics', current).href};
      const calls = [];
      vm.runInNewContext(script, {
        URL,
        document: {getElementById: id => {assert.equal(id, 'moved-target'); return link;}},
        location: {search: current.search, replace: url => calls.push(url)},
      });
      const expected = `https://docs.example.test/en/latest/workspace/deliverables/index.html${query}#statistics`;
      assert.deepEqual(calls, [expected]);
      assert.equal(link.href, expected);
    });
  }
}
