---
---
var docs =
[
{% for post in site.pages %}
{% if post.layout == 'kanji' or post.layout == 'kanji-remain' %}
  {% include post.json %},
{% endif %}  
{% endfor %}
];

/**
 * RMTK VN — Multi-mode Kanji Search Engine
 * Supports: kanji character, frame number, Hán-Việt, English keyword
 */
var SearchEngine = (function() {
  'use strict';

  // Detect if a string contains CJK characters
  function isCJK(str) {
    return /[\u4E00-\u9FFF\u3400-\u4DBF]/.test(str);
  }

  // Detect if a string is a frame number query (pure digits or #digits)
  function isFrameNumber(str) {
    return /^#?\d+$/.test(str.trim());
  }

  // Detect Vietnamese diacritics (Hán-Việt search)
  function hasVietnameseDiacritics(str) {
    return /[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]/i.test(str);
  }

  // Normalize string for comparison
  function normalize(str) {
    if (str == null) return '';
    return String(str).toLowerCase().trim();
  }

  // Remove Vietnamese diacritics for loose matching
  function removeVietnameseTones(str) {
    if (str == null) return '';
    return String(str).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
  }

  // Search by kanji character
  function searchByKanji(query) {
    var results = [];
    for (var i = 0; i < docs.length; i++) {
      if (docs[i].kanji && docs[i].kanji.indexOf(query) !== -1) {
        results.push({ doc: docs[i], score: 100, matchType: 'kanji' });
      }
    }
    return results;
  }

  // Search by frame number
  function searchByFrame(query) {
    var num = query.replace('#', '').trim();
    var results = [];
    for (var i = 0; i < docs.length; i++) {
      if (docs[i].v4 && String(docs[i].v4) === num) {
        results.push({ doc: docs[i], score: 100, matchType: 'frame' });
      } else if (docs[i].id && String(docs[i].id) === num) {
        results.push({ doc: docs[i], score: 100, matchType: 'frame' });
      }
    }
    return results;
  }

  // Search by Hán-Việt reading
  function searchByHanViet(query) {
    var q = normalize(query);
    var qNoTone = removeVietnameseTones(query);
    var results = [];

    for (var i = 0; i < docs.length; i++) {
      var hv = normalize(docs[i].hanviet);
      if (!hv) continue;

      if (hv === q) {
        results.push({ doc: docs[i], score: 100, matchType: 'hanviet-exact' });
      } else if (hv.indexOf(q) === 0) {
        results.push({ doc: docs[i], score: 80, matchType: 'hanviet-prefix' });
      } else {
        // Split multi-word Hán-Việt readings (e.g., "nhất, nhị")
        var parts = hv.split(/[,\s]+/);
        var matched = false;
        for (var j = 0; j < parts.length; j++) {
          if (parts[j] === q) {
            results.push({ doc: docs[i], score: 90, matchType: 'hanviet-word' });
            matched = true;
            break;
          } else if (parts[j].indexOf(q) === 0) {
            results.push({ doc: docs[i], score: 70, matchType: 'hanviet-word-prefix' });
            matched = true;
            break;
          }
        }
        if (!matched && hv.indexOf(q) !== -1) {
          results.push({ doc: docs[i], score: 50, matchType: 'hanviet-substring' });
        }
        // Toneless fallback
        if (!matched) {
          var hvNoTone = removeVietnameseTones(docs[i].hanviet);
          if (hvNoTone.indexOf(qNoTone) !== -1) {
            results.push({ doc: docs[i], score: 30, matchType: 'hanviet-toneless' });
          }
        }
      }
    }
    return results;
  }

  // Search by keyword (Vietnamese primary + English fallback)
  function searchByKeyword(query) {
    var q = normalize(query);
    var results = [];

    for (var i = 0; i < docs.length; i++) {
      var kw = normalize(docs[i].keyword);
      var el = normalize(docs[i].elements);
      var hv = normalize(docs[i].hanviet);
      var score = 0;
      var matchType = '';

      // Keyword matching (highest priority)
      score = matchKeyword(kw, q);
      if (score > 0) { matchType = 'keyword'; }

      // Hán-Việt matching (secondary)
      if (score === 0 && hv && hv.indexOf(q) !== -1) {
        score = 35;
        matchType = 'hanviet-fallback';
      }

      // Elements matching
      if (score === 0 && el) {
        score = matchElements(el, q);
        if (score > 0) { matchType = 'elements'; }
      }

      if (score > 0) {
        results.push({ doc: docs[i], score: score, matchType: matchType });
      }
    }

    return results;
  }

  // Score a keyword match
  function matchKeyword(kw, q) {
    if (kw === q) return 100;
    if (kw.indexOf(q) === 0) return 85;

    var words = kw.split(/[\s\-\(\),]+/);
    for (var j = 0; j < words.length; j++) {
      if (words[j] === q) return 75;
      if (words[j].indexOf(q) === 0) return 65;
    }
    if (kw.indexOf(q) !== -1) return 45;
    return 0;
  }

  // Score an elements match
  function matchElements(el, q) {
    if (el === q) return 30;
    var elWords = el.split(/[\s\-\(\),]+/);
    for (var k = 0; k < elWords.length; k++) {
      if (elWords[k] === q) return 25;
      if (elWords[k].indexOf(q) === 0) return 20;
    }
    if (el.indexOf(q) !== -1) return 10;
    return 0;
  }

  // Main search dispatcher
  function search(query) {
    if (!query || query.trim().length === 0) return [];

    var q = query.trim();
    var results;

    if (isCJK(q)) {
      results = searchByKanji(q);
    } else if (isFrameNumber(q)) {
      results = searchByFrame(q);
    } else if (hasVietnameseDiacritics(q)) {
      results = searchByHanViet(q);
    } else {
      results = searchByKeyword(q);
    }

    // Sort by score descending, then by frame number ascending
    results.sort(function(a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return (parseInt(a.doc.v4) || 9999) - (parseInt(b.doc.v4) || 9999);
    });

    // Cap at 50 results
    return results.slice(0, 50);
  }

  return {
    search: search,
    isCJK: isCJK,
    isFrameNumber: isFrameNumber,
    hasVietnameseDiacritics: hasVietnameseDiacritics
  };
})();
