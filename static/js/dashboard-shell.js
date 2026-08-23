(function () {
  var sidebar = document.getElementById('dashSidebar');
  var backdrop = document.getElementById('dashSidebarBackdrop');
  var openBtn = document.getElementById('dashSidebarOpen');
  var closeBtn = document.getElementById('dashSidebarClose');

  function setSidebar(open) {
    if (!sidebar) return;
    sidebar.classList.toggle('show', open);
    if (backdrop) backdrop.classList.toggle('show', open);
  }

  if (openBtn) openBtn.addEventListener('click', function () { setSidebar(true); });
  if (closeBtn) closeBtn.addEventListener('click', function () { setSidebar(false); });
  if (backdrop) backdrop.addEventListener('click', function () { setSidebar(false); });

  var items = Array.prototype.slice.call(document.querySelectorAll('.dash-course-item'));

  var totals = items.reduce(function (acc, el) {
    acc.lessons += parseInt(el.dataset.lessons, 10) || 0;
    acc.students += parseInt(el.dataset.students, 10) || 0;
    return acc;
  }, { lessons: 0, students: 0 });

  Object.keys(totals).forEach(function (key) {
    var target = document.querySelector('[data-stat="' + key + '"]');
    if (target) target.textContent = totals[key];
  });

  var search = document.getElementById('dashCourseSearch');
  var emptyState = document.getElementById('dashCourseEmptySearch');

  if (search && items.length) {
    search.addEventListener('input', function () {
      var term = search.value.trim().toLowerCase();
      var visible = 0;
      items.forEach(function (el) {
        var match = !term || el.dataset.title.indexOf(term) !== -1;
        el.classList.toggle('d-none', !match);
        if (match) visible++;
      });
      if (emptyState) emptyState.classList.toggle('d-none', visible !== 0);
    });
  }
})();
