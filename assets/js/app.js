---
---
$(function() {
  var $input = $('#search-query');
  var $results = $('#search-results');
  var $entries = $('#search-results .entries');
  var $count = $('#result-count');
  var $chips = $('.filter-chip');
  var activeFilter = 'all';
  var debounceTimer = null;
  var selectedIndex = -1;

  // Filter chip handling
  $chips.on('click', function() {
    $chips.removeClass('active');
    $(this).addClass('active');
    activeFilter = $(this).data('filter');
    doSearch();
  });

  // Search on keyup with debounce
  $input.on('keyup', function(e) {
    if (e.keyCode === 40 || e.keyCode === 38 || e.keyCode === 13) {
      handleKeyNav(e);
      return;
    }
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(doSearch, 120);
  });

  // Search button click
  $('#search-button').on('click', function() {
    doSearch();
    return false;
  });

  // Clear button
  $('#search-clear').on('click', function() {
    $input.val('').focus();
    $results.hide();
    $entries.empty();
    $count.text('');
    selectedIndex = -1;
  });

  // Keyboard shortcut: "/" to focus search
  $(document).on('keydown', function(e) {
    if (e.key === '/' && !$input.is(':focus')) {
      e.preventDefault();
      $input.focus();
    }
    if (e.key === 'Escape') {
      $input.blur();
      $results.hide();
    }
  });

  function doSearch() {
    var query = $input.val().trim();
    selectedIndex = -1;

    if (query.length === 0) {
      $results.hide();
      $entries.empty();
      $count.text('');
      return;
    }

    var minLen = SearchEngine.isFrameNumber(query) || SearchEngine.isCJK(query) ? 1 : 2;
    if (query.length < minLen) {
      $results.hide();
      $entries.empty();
      $count.text('');
      return;
    }

    var results = SearchEngine.search(query);

    // Apply filter
    if (activeFilter !== 'all') {
      results = results.filter(function(r) {
        switch (activeFilter) {
          case 'keyword': return r.matchType.indexOf('keyword') === 0;
          case 'hanviet': return r.matchType.indexOf('hanviet') === 0;
          case 'frame': return r.matchType === 'frame';
          default: return true;
        }
      });
    }

    $entries.empty();

    if (results.length > 0) {
      var countText = '<span class="count-number">' + results.length + '</span> kết quả' + (results.length >= 50 ? '+' : '');
      $count.html(countText);

      $.each(results, function(idx, item) {
        var card = buildResultCard(item.doc, item.matchType, query);
        $entries.append(card);
      });
    } else {
      $count.text('');
      $entries.append(
        '<div class="no-results">' +
        '  <div class="no-results-icon">🔍</div>' +
        '  <div class="no-results-text">Không tìm thấy Kanji nào</div>' +
        '  <div class="no-results-hint">Thử tìm bằng từ khóa, Hán-Việt, số frame (#1), hoặc dán trực tiếp chữ Kanji</div>' +
        '</div>'
      );
    }

    $results.show();
  }

  function buildResultCard(doc, matchType, query) {
    var kanji = String(doc.kanji || '');
    var keyword = String(doc.keyword || '');
    var hanviet = String(doc.hanviet || '');
    var elements = String(doc.elements || '');
    var v4 = String(doc.v4 || doc.id || '');
    var onYomi = String(doc.onYomi || '');
    var kunYomi = String(doc.kunYomi || '');

    var url = './' + kanji.charAt(0) + '/index.html';

    var highlightedKeyword = highlightMatch(keyword, query);
    var highlightedHanViet = highlightMatch(hanviet, query);

    // Badge
    var badge = '';
    if (matchType.indexOf('hanviet') === 0) {
      badge = '<span class="match-badge badge-hanviet">Hán-Việt</span>';
    } else if (matchType === 'frame') {
      badge = '<span class="match-badge badge-frame">Frame</span>';
    } else if (matchType === 'kanji') {
      badge = '<span class="match-badge badge-kanji">Kanji</span>';
    } else if (matchType.indexOf('elements') === 0) {
      badge = '<span class="match-badge badge-elements">Thành phần</span>';
    }

    // Readings
    var readingsHtml = '';
    if (onYomi || kunYomi) {
      readingsHtml = '<div class="result-readings">';
      if (onYomi) readingsHtml += '<span class="reading on-yomi" title="On-Yomi">音 ' + onYomi + '</span>';
      if (kunYomi) readingsHtml += '<span class="reading kun-yomi" title="Kun-Yomi">訓 ' + kunYomi + '</span>';
      readingsHtml += '</div>';
    }

    // Elements preview (show first 3)
    var elementsHtml = '';
    if (elements && elements !== 'null') {
      var elArr = elements.split(',');
      var preview = elArr.slice(0, 3).map(function(e) { return e.trim(); }).join(' · ');
      if (elArr.length > 3) preview += ' +' + (elArr.length - 3);
      elementsHtml = '<div class="result-elements">' + preview + '</div>';
    }

    return '<a href="' + url + '" class="result-card" data-index="' + v4 + '">' +
      '<div class="result-kanji">' + kanji + '</div>' +
      '<div class="result-info">' +
      '  <div class="result-header">' +
      '    <span class="result-keyword">' + highlightedKeyword + '</span>' +
      '    <span class="result-frame">#' + v4 + '</span>' +
      '    ' + badge +
      '  </div>' +
      (hanviet ? '  <div class="result-hanviet">' + highlightedHanViet + '</div>' : '') +
      elementsHtml +
      readingsHtml +
      '</div>' +
      '</a>';
  }

  function highlightMatch(text, query) {
    if (text == null) return '';
    text = String(text);
    if (!query) return text;
    var escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    var regex = new RegExp('(' + escaped + ')', 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  function handleKeyNav(e) {
    var $cards = $entries.find('.result-card');
    if ($cards.length === 0) return;

    if (e.keyCode === 40) {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, $cards.length - 1);
    } else if (e.keyCode === 38) {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
    } else if (e.keyCode === 13) {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < $cards.length) {
        window.location.href = $($cards[selectedIndex]).attr('href');
      }
      return;
    }

    $cards.removeClass('selected');
    if (selectedIndex >= 0) {
      var $selected = $($cards[selectedIndex]);
      $selected.addClass('selected');
      $selected[0].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }
});
