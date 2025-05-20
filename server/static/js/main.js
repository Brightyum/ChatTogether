let centerX = window.innerWidth / 2;
let centerY = window.innerHeight / 2;

const blobs = [
  {
    el: null,
    selector: '.blob1',
    startOffsetX: -window.innerWidth * 0.45,
    startOffsetY: -window.innerHeight * 0.45,
    radius: 100,
    speed: 0.001,
    phase: 0
  },
  {
    el: null,
    selector: '.blob2',
    startOffsetX: window.innerWidth * 0.45,
    startOffsetY: -window.innerHeight * 0.45,
    radius: 100,
    speed: 0.001,
    phase: 120
  },
  {
    el: null,
    selector: '.blob3',
    startOffsetX: 0,
    startOffsetY: window.innerHeight * 0.5,
    radius: 100,
    speed: 0.001,
    phase: 240
  }
];

window.addEventListener('DOMContentLoaded', () => {
  // ✅ 전역 blobs 배열에서 el 연결만 수행
  blobs.forEach(b => {
    b.el = document.querySelector(b.selector);
    if (b.el) b.el.style.opacity = 0; // 초기엔 숨김
  });

  // 늑대 실루엣 요소
  const wolf = document.getElementById('wolf-outline');
  const hero = document.getElementById('hero-content');

  // 1. 늑대 실루엣 애니메이션 시작
  setTimeout(() => {
    wolf.style.animationPlayState = 'running';
  }, 500);

  // 2. 늑대 사라짐
  setTimeout(() => {
    wolf.style.opacity = 0;
  }, 4000);

  // 3. blob 다시 등장 (회전 준비)
  setTimeout(() => {
    blobs.forEach(b => {
      if (b.el) b.el.style.opacity = 1;
    });

    // ✅ 여기서 애니메이션 시작
    requestAnimationFrame(animate);
  }, 5500);

  // 4. 텍스트 등장
  setTimeout(() => {
    hero.classList.add('show');
  }, 6500);
});

function animate(time) {
  const cycleDuration = 12000;
  const driftDuration = 4000;
  const mergeDuration = 4000;
  const separateDuration = 4000;

  const cycleTime = time % cycleDuration;

  let mergeFactor = 0;
  if (cycleTime < driftDuration) mergeFactor = 0;
  else if (cycleTime < driftDuration + mergeDuration)
    mergeFactor = (cycleTime - driftDuration) / mergeDuration;
  else if (cycleTime < driftDuration + mergeDuration + separateDuration)
    mergeFactor = 1 - (cycleTime - driftDuration - mergeDuration) / separateDuration;

  blobs.forEach(b => {
    if (!b.el) return;

    const rotateCenterX = centerX * mergeFactor + (centerX + b.startOffsetX) * (1 - mergeFactor);
    const rotateCenterY = centerY * mergeFactor + (centerY + b.startOffsetY) * (1 - mergeFactor);

    const x = rotateCenterX + Math.cos(time * b.speed + b.phase) * b.radius;
    const y = rotateCenterY + Math.sin(time * b.speed + b.phase) * b.radius;

    b.el.style.transform = `translate(${x}px, ${y}px)`;
    b.el.style.opacity = 0.4 + 0.6 * mergeFactor;
  });

  requestAnimationFrame(animate);
}

// 텍스트 등장 (예: 늑대가 사라진 후)
setTimeout(() => {
  document.getElementById('hero-content').classList.add('show');
}, 6500);
