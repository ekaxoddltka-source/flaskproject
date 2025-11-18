// info.js (권장 — 교체용)
document.addEventListener('DOMContentLoaded', () => {
  // --- 탭 버튼 / 탭 패널 제어 ---
  const tabButtons = document.querySelectorAll('.sidebar-tabs .tab-button');
  const tabPanels = document.querySelectorAll('.sidebar .tab-panel');

  function resetTabs() {
    tabButtons.forEach(btn => {
      btn.setAttribute('aria-selected', 'false');
      btn.classList.remove('active');
    });
    tabPanels.forEach(panel => panel.classList.add('hidden')); // CSS에 hidden 처리 담당
  }

  function showTab(targetId) {
    resetTabs();
    const btn = document.querySelector(`.tab-button[data-target="${targetId}"]`);
    const panel = document.getElementById(targetId);
    if (btn) {
      btn.setAttribute('aria-selected', 'true');
      btn.classList.add('active');
    }
    if (panel) panel.classList.remove('hidden');
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => showTab(btn.dataset.target));
  });

  // --- info-list (공지/약관/개인정보) 제어 ---
  const list = document.querySelector('.info-list');
  if (!list) {
    // info-list가 아예 없으면 여기서 종료 (에러 로그 확인용)
    console.warn('[info.js] .info-list 미발견 — info.js 초기화 일부만 동작함');
    showTab('panel-info'); // 그래도 탭은 공지로 열어둠
    return;
  }

  const links = Array.from(list.querySelectorAll('a[data-content]'));
  const panels = {
    notice: document.getElementById('notice-panel'),
    terms:  document.getElementById('terms-panel'),
    privacy: document.getElementById('privacy-panel')
  };

  function resetInfo() {
    Object.values(panels).forEach(p => p && p.classList.add('hidden'));
    links.forEach(a => {
      a.parentElement?.classList.remove('selected');
      a.classList.remove('active');
    });
  }

  function showPanel(key) {
    const panel = panels[key];
    if (!panel) return;
    resetInfo();
    panel.classList.remove('hidden');

    const link = list.querySelector(`a[data-content="${key}"]`);
    if (link) {
      link.parentElement.classList.add('selected'); // li에 selected
      link.classList.add('active');                // a에도 active (CSS 호환성 확보)
    }
    // 공지 리스트를 보여줄 때 사이드바의 공지 탭이 열려있도록 보장
    showTab('panel-info');
  }

  links.forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      showPanel(a.dataset.content);
    });
  });

  // --- 초기 상태 ---
  // 모든 탭/패널을 hidden 처리한 뒤, 공지사항 탭/패널을 보이게 설정
  resetTabs();
  resetInfo();
  // ✅ URL 파라미터 기반 자동 패널 열기
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab");
  if (tab && ["notice", "terms", "privacy"].includes(tab)) {
    showTab('panel-info');  // 사이드바는 info 탭 열기
    showPanel(tab);         // 해당 패널 표시
  } else {
    showTab('panel-info');  // 기본: 공지사항 탭
    showPanel('notice');
  }
});
