// 已读状态：localStorage 单一来源（每设备/浏览器独立，不同步）
(function() {
  'use strict';

  var KEY = 'auto-trend-read';

  // 读取已读日期集合，存储不可用时降级为空集
  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      return new Set(raw ? JSON.parse(raw) : []);
    } catch (e) {
      return new Set();
    }
  }

  // 写入已读日期集合，失败静默（隐私模式等场景不阻塞交互）
  function save(set) {
    try {
      localStorage.setItem(KEY, JSON.stringify(Array.from(set)));
    } catch (e) {}
  }

  // 切换某日期的已读状态，返回切换后是否已读
  function toggle(dateStr) {
    var set = load();
    if (set.has(dateStr)) { set.delete(dateStr); } else { set.add(dateStr); }
    save(set);
    return set.has(dateStr);
  }

  window.ReadState = { load: load, save: save, toggle: toggle };
})();
