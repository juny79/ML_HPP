/* =============================================

   설정 & 전역 상태

   ============================================= */

const API_BASE = 'http://localhost:5000/api';



const state = {

    token:           localStorage.getItem('token') || null,

    user:            JSON.parse(localStorage.getItem('user') || 'null'),

    currentTab:      'leaderboard',

    leaderboardPage: 1,

    mySubsPage:      1,

    selectedFile:    null,

    pollingTimer:    null,

};



/* =============================================

   초기화

   ============================================= */

document.addEventListener('DOMContentLoaded', () => {

    initNavTabs();

    updateAuthUI();

    loadLeaderboard();



    if (state.token) {

        loadDailyLimit();

        loadMyRank();

        loadMySubmissions();

    }

});



/* =============================================

   탭 네비게이션

   ============================================= */

function initNavTabs() {

    document.querySelectorAll('.nav-link[data-tab]').forEach(link => {

        link.addEventListener('click', e => {

            e.preventDefault();

            switchTab(link.dataset.tab);

        });

    });

}



function switchTab(tabName) {

    // 탭 버튼 활성화

    document.querySelectorAll('.nav-link[data-tab]').forEach(l => {

        l.classList.toggle('active', l.dataset.tab === tabName);

    });



    // 탭 콘텐츠 전환

    document.querySelectorAll('.tab-content').forEach(section => {

        section.classList.add('hidden');

    });

    document.getElementById(`tab-${tabName}`).classList.remove('hidden');



    state.currentTab = tabName;



    // 탭별 초기화

    if (tabName === 'submit') {

        if (!state.token) {

            show('submit-login-required');

            hide('submit-form-wrapper');

        } else {

            hide('submit-login-required');

            show('submit-form-wrapper');

            loadDailyLimit();

        }

    }



    if (tabName === 'my-submissions') {

        if (!state.token) {

            show('my-submissions-login-required');

            hide('my-submissions-wrapper');

        } else {

            hide('my-submissions-login-required');

            show('my-submissions-wrapper');

            loadMySubmissions();

        }

    }

}



/* =============================================

   인증 UI 업데이트

   ============================================= */

function updateAuthUI() {

    if (state.token && state.user) {

        hide('auth-buttons');

        show('user-info');

        document.getElementById('username-display').textContent =

            state.user.team_name || state.user.username;

    } else {

        show('auth-buttons');

        hide('user-info');

    }

}



/* =============================================

   API 헬퍼

   ============================================= */

async function apiFetch(endpoint, options = {}) {

    const headers = { 'Content-Type': 'application/json', ...options.headers };



    if (state.token) {

        headers['Authorization'] = `Bearer ${state.token}`;

    }



    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });



    // 401 → 자동 로그아웃

    if (res.status === 401) {

        logout(false);

        showToast('세션이 만료되었습니다. 다시 로그인해주세요.', 

        'warning');

        return null;

    }



    return res.json();

}



async function apiUpload(endpoint, formData) {

    const headers = {};

    if (state.token) {

        headers['Authorization'] = `Bearer ${state.token}`;

    }



    const res = await fetch(`${API_BASE}${endpoint}`, {

        method:  'POST',

        headers,

        body:    formData,

    });



    return res.json();

}



/* =============================================

   인증 - 로그인

   ============================================= */

async function login() {

    const username = document.getElementById('login-username').value.trim();

    const password = document.getElementById('login-password').value;



    if (!username || !password) {

        showError('login-error', '사용자명과 비밀번호를 입력해주세요.');

        return;

    }



    try {

        const data = await apiFetch('/auth/login', {

            method: 'POST',

            body:   JSON.stringify({ username, password }),

        });



        if (!data || !data.success) {

            showError('login-error', data?.message || '로그인에 실패했습니다.');

            return;

        }



        // 토큰 & 유저 저장

        state.token = data.access_token;

        state.user  = data.user;

        localStorage.setItem('token', data.access_token);

        localStorage.setItem('user',  JSON.stringify(data.user));



        closeModal('login-modal');

        updateAuthUI();

        loadDailyLimit();

        loadMyRank();

        loadLeaderboard();



        showToast(`${data.user.username}님, 환영합니다! 🎉`, 'success');



    } catch (err) {

        showError('login-error', '서버 연결에 실패했습니다.');

    }

}



/* =============================================

   인증 - 회원가입

   ============================================= */

async function register() {

    const username  = document.getElementById('reg-username').value.trim();

    const email     = document.getElementById('reg-email').value.trim();

    const teamName  = document.getElementById('reg-teamname').value.trim();

    const password  = document.getElementById('reg-password').value;

    const passwordC = document.getElementById('reg-password-confirm').value;



    // 유효성 검사

    if (!username || !email || !password) {

        showError('register-error', '필수 항목을 모두 입력해주세요.');

        return;

    }



    if (password !== passwordC) {

        showError('register-error', '비밀번호가 일치하지 않습니다.');

        return;

    }



    if (password.length < 8) {

        showError('register-error', '비밀번호는 8자 이상이어야 합니다.');

        return;

    }



    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {

        showError('register-error', '올바른 이메일 형식을 입력해주세요.');

        return;

    }



    try {

        const data = await apiFetch('/auth/register', {

            method: 'POST',

            body:   JSON.stringify({ username, email, password, team_name: teamName }),

        });



        if (!data || !data.success) {

            showError('register-error', data?.message || '회원가입에 실패했습니다.');

            return;

        }



        // 토큰 & 유저 저장

        state.token = data.access_token;

        state.user  = data.user;

        localStorage.setItem('token', data.access_token);

        localStorage.setItem('user',  JSON.stringify(data.user));



        closeModal('register-modal');

        updateAuthUI();

        loadDailyLimit();

        loadLeaderboard();



        showToast('회원가입이 완료되었습니다! 🎉', 'success');



    } catch (err) {

        showError('register-error', '서버 연결에 실패했습니다.');

    }

}



/* =============================================

   인증 - 로그아웃

   ============================================= */

function logout(showMsg = true) {

    state.token = null;

    state.user  = null;

    localStorage.removeItem('token');

    localStorage.removeItem('user');



    updateAuthUI();

    loadLeaderboard();



    // 내 순위 카드 숨기기

    hide('my-rank-card');



    if (showMsg) showToast('로그아웃 되었습니다.', 'warning');

}



/* =============================================

   리더보드 로드

   ============================================= */

async function loadLeaderboard(page = 1) {

    state.leaderboardPage = page;



    const tbody = document.getElementById('leaderboard-body');

    tbody.innerHTML = `

        <tr>

            <td colspan="5" class="loading-cell">

                <i class="fas fa-spinner fa-spin"></i> 로딩 중...

            </td>

        </tr>`;



    try {

        const data = await apiFetch(

            `/leaderboard/public?page=${page}&per_page=20`

        );



        if (!data || !data.success) {

            tbody.innerHTML = `

                <tr>

                    <td colspan="5" class="loading-cell">

                        데이터를 불러오지 못했습니다.

                    </td>

                </tr>`;

            return;

        }



        const { leaderboard, total, pages } = data.data;



        // 통계 업데이트

        document.getElementById('total-participants').textContent =

            total.toLocaleString();



        // 마지막 업데이트 시각

        document.getElementById('last-update').textContent =

            new Date().toLocaleTimeString('ko-KR');



        // 테이블 렌더링

        if (leaderboard.length === 0) {

            tbody.innerHTML = `

                <tr>

                    <td colspan="5" class="loading-cell">

                        아직 제출 내역이 없습니다.

                    </td>

                </tr>`;

        } else {

            tbody.innerHTML = leaderboard.map(row => {

                const isMe    = state.user?.username === row.username;

                const rankIcon = getRankIcon(row.rank);



                return `

                <tr class="${isMe ? 'my-row' : ''}">

                    <td class="rank-cell ${getRankClass(row.rank)}">

                        ${rankIcon}

                    </td>

                    <td>

                        <strong>${escapeHtml(row.team_name)}</strong>

                        ${isMe ? '<span class="rank-badge" style="margin-left:6px">나</span>' : ''}

                    </td>

                    <td>

                        <span class="rmse-value">${row.public_rmse.toFixed(4)}</span>

                    </td>

                    <td>${row.submission_count}회</td>

                    <td style="color:var(--text-muted); font-size:.85rem">

                        ${formatDate(row.achieved_at)}

                    </td>

                </tr>`;

            }).join('');

        }



        // 총 제출 수 업데이트 (전체 합산)

        const totalSubs = leaderboard.reduce(

            (acc, r) => acc + r.submission_count, 0

        );

        document.getElementById('total-submissions').textContent =

            totalSubs.toLocaleString();



        // 페이지네이션 렌더링

        renderPagination(

            'leaderboard-pagination',

            page,

            pages,

            loadLeaderboard

        );



    } catch (err) {

        tbody.innerHTML = `

            <tr>

                <td colspan="5" class="loading-cell">

                    서버 연결에 실패했습니다.

                </td>

            </tr>`;

    }

}



/* =============================================

   내 순위 로드

   ============================================= */

async function loadMyRank() {

    if (!state.token) return;



    try {

        const data = await apiFetch('/leaderboard/my-rank');

        if (!data || !data.success) return;



        const { rank, public_rmse, total_participants } = data.data;



        if (rank) {

            show('my-rank-card');

            document.getElementById('my-rank-value').textContent  = `#${rank}`;

            document.getElementById('my-rmse-value').textContent  =

                public_rmse?.toFixed(4) ?? '-';

            document.getElementById('my-total-value').textContent =

                `${total_participants}명 중`;



            // 네비게이션 뱃지 업데이트

            document.getElementById('rank-badge').textContent = `#${rank}`;

        }



    } catch (err) {

        console.error('내 순위 로드 실패:', err);

    }

}



/* =============================================

   일일 제출 한도 로드

   ============================================= */

async function loadDailyLimit() {

    if (!state.token) return;



    try {

        const data = await apiFetch('/daily-limit');

        if (!data || !data.success) return;



        const { max_per_day, remaining } = data.data;

        const used = max_per_day - remaining;



        document.getElementById('remaining-count').textContent = remaining;

        document.getElementById('max-count').textContent       = max_per_day;



        // 프로그레스 바 (남은 횟수 비율)

        const pct = (remaining / max_per_day) * 100;

        document.getElementById('limit-bar-fill').style.width = `${pct}%`;



        // 색상 변경 (남은 횟수 적을수록 빨간색)

        const fill = document.getElementById('limit-bar-fill');

        if (remaining === 0) {

            fill.style.background = 'var(--danger)';

        } else if (remaining <= 2) {

            fill.style.background = 'var(--warning)';

        } else {

            fill.style.background =

                'linear-gradient(90deg, var(--primary), #7c3aed)';

        }



    } catch (err) {

        console.error('일일 한도 로드 실패:', err);

    }

}



/* =============================================

   파일 업로드 핸들러

   ============================================= */

function handleDragOver(e) {

    e.preventDefault();

    document.getElementById('upload-area').classList.add('dragover');

}



function handleDragLeave(e) {

    document.getElementById('upload-area').classList.remove('dragover');

}



function handleDrop(e) {

    e.preventDefault();

    document.getElementById('upload-area').classList.remove('dragover');



    const file = e.dataTransfer.files[0];

    if (file) setSelectedFile(file);

}



function handleFileSelect(e) {

    const file = e.target.files[0];

    if (file) setSelectedFile(file);

}



function setSelectedFile(file) {

    // CSV 확장자 확인

    if (!file.name.endsWith('.csv')) {

        showToast('CSV 파일만 업로드 가능합니다.', 'error');

        return;

    }



    // 파일 크기 확인 (16MB)

    if (file.size > 16 * 1024 * 1024) {

        showToast('파일 크기는 16MB 이하여야 합니다.', 'error');

        return;

    }



    state.selectedFile = file;



    // 파일 정보 표시

    document.getElementById('file-name').textContent = file.name;

    document.getElementById('file-size').textContent =

        `(${(file.size / 1024).toFixed(1)} KB)`;



    show('file-info');

    document.getElementById('submit-btn').disabled = false;

    hide('submit-result');

}



function clearFile() {

    state.selectedFile = null;

    document.getElementById('file-input').value = '';

    document.getElementById('file-name').textContent = '';



    hide('file-info');

    document.getElementById('submit-btn').disabled = true;

}



/* =============================================

   파일 제출

   ============================================= */

async function submitFile() {

    if (!state.selectedFile) {

        showToast('파일을 선택해주세요.', 'warning');

        return;

    }



    if (!state.token) {

        openModal('login-modal');

        return;

    }



    const description = document.getElementById('description').value.trim();

    const formData    = new FormData();

    formData.append('file',        state.selectedFile);

    formData.append('description', description);



    // 제출 버튼 비활성화

    const submitBtn = document.getElementById('submit-btn');

    submitBtn.disabled   = true;

    submitBtn.innerHTML  =

        '<i class="fas fa-spinner fa-spin"></i> 제출 중...';



    try {

        const data = await apiUpload('/submit', formData);



        if (!data || !data.success) {

            showToast(data?.message || '제출에 실패했습니다.', 'error');

            submitBtn.disabled  = false;

            submitBtn.innerHTML =

                '<i class="fas fa-paper-plane"></i> 제출하기';

            return;

        }



        showToast('제출 완료! 채점 중입니다...', 'success');

        clearFile();

        loadDailyLimit();



        // 채점 진행 모달 표시 & 폴링 시작

        openScoringModal(data.submission_id);



    } catch (err) {

        showToast('서버 연결에 실패했습니다.', 'error');

        submitBtn.disabled  = false;

        submitBtn.innerHTML =

            '<i class="fas fa-paper-plane"></i> 제출하기';

    } finally {

        submitBtn.disabled  = false;

        submitBtn.innerHTML =

            '<i class="fas fa-paper-plane"></i> 제출하기';

    }

}



/* =============================================

   채점 진행 모달 & 폴링

   ============================================= */

function openScoringModal(submissionId) {

    openModal('scoring-modal');



    const steps = [

        { msg: '파일 검증 중...',    pct: 20  },

        { msg: 'RMSE 계산 중...',    pct: 50  },

        { msg: '리더보드 업데이트...', pct: 80  },

        { msg: '완료!',              pct: 100 },

    ];



    let stepIdx = 0;



    // 진행 애니메이션

    const animTimer = setInterval(() => {

        if (stepIdx < steps.length) {

            document.getElementById('scoring-progress').style.width =

                `${steps[stepIdx].pct}%`;

            document.getElementById('scoring-status').textContent =

                steps[stepIdx].msg;

            stepIdx++;

        }

    }, 800);



    // 상태 폴링 (2초 간격)

    let pollCount = 0;

    state.pollingTimer =

    setInterval(async () => {

        pollCount++;



        // 최대 30회 폴링 (60초)

        if (pollCount > 30) {

            clearInterval(state.pollingTimer);

            clearInterval(animTimer);

            closeModal('scoring-modal');

            showToast('채점 시간이 초과되었습니다. 잠시 후 확인해주세요.', 'warning');

            return;

        }



        try {

            const data = await apiFetch(

                `/submissions/${submissionId}/status`

            );



            if (!data || !data.success) return;



            const { status, public_rmse, error } = data.data;



            if (status === 'completed') {

                clearInterval(state.pollingTimer);

                clearInterval(animTimer);

                closeModal('scoring-modal');



                // 결과 표시

                showSubmitResult(public_rmse);



                // 리더보드 & 내 순위 갱신

                loadLeaderboard();

                loadMyRank();

                loadMySubmissions();



                showToast(

                    `채점 완료! Public RMSE: ${public_rmse.toFixed(4)}`,

                    'success'

                );



            } else if (status === 'failed') {

                clearInterval(state.pollingTimer);

                clearInterval(animTimer);

                closeModal('scoring-modal');



                showToast(

                    `채점 실패: ${error || '알 수 없는 오류'}`,

                    'error'

                );

                loadMySubmissions();

            }



        } catch (err) {

            console.error('폴링 오류:', err);

        }

    }, 2000);

}



function showSubmitResult(publicRmse) {

    const resultDiv = document.getElementById('submit-result');

    resultDiv.classList.remove('hidden');

    resultDiv.innerHTML = `

        <div class="result-title">

            <i class="fas fa-check-circle" style="color:var(--success)"></i>

            채점 완료

        </div>

        <div class="result-score">${publicRmse.toFixed(4)}</div>

        <div class="result-meta">

            Public RMSE (전체 데이터의 50% 기준)

        </div>

        <div style="margin-top:12px">

            <button

                class="btn btn-outline btn-sm"

                onclick="switchTab('leaderboard')"

            >

                <i class="fas fa-trophy"></i> 리더보드 확인

            </button>

            <button

                class="btn btn-outline btn-sm"

                style="margin-left:8px"

                onclick="switchTab('my-submissions')"

            >

                <i class="fas fa-list"></i> 내 제출 목록

            </button>

        </div>

    `;

}



/* =============================================

   내 제출 목록 로드

   ============================================= */

async function loadMySubmissions(page = 1) {

    if (!state.token) return;



    state.mySubsPage = page;



    const tbody = document.getElementById('my-submissions-body');

    tbody.innerHTML = `

        <tr>

            <td colspan="6" class="loading-cell">

                <i class="fas fa-spinner fa-spin"></i> 로딩 중...

            </td>

        </tr>`;



    try {

        const data = await apiFetch(

            `/submissions?page=${page}&per_page=10`

        );



        if (!data || !data.success) {

            tbody.innerHTML = `

                <tr>

                    <td colspan="6" class="loading-cell">

                        데이터를 불러오지 못했습니다.

                    </td>

                </tr>`;

            return;

        }



        const { submissions, total, pages } = data.data;



        if (submissions.length === 0) {

            tbody.innerHTML = `

                <tr>

                    <td colspan="6" class="loading-cell">

                        아직 제출 내역이 없습니다.

                    </td>

                </tr>`;

            return;

        }



        tbody.innerHTML = submissions.map((sub, idx) => {

            const globalIdx = (page - 1) * 10 + idx + 1;

            const statusBadge = getStatusBadge(sub.status);

            const rmseDisplay = sub.public_rmse !== null

                ? `<span class="rmse-value">${sub.public_rmse.toFixed(4)}</span>`

                : `<span style="color:var(--text-muted)">-</span>`;



            const selectBtn = sub.status === 'completed'

                ? `<button

                        class="btn-select ${sub.is_selected ? 'selected' : ''}"

                        onclick="selectSubmission(${sub.id})"

                    >

                        ${sub.is_selected

                            ? '<i class="fas fa-check"></i> 선택됨'

                            : '최종 선택'}

                    </button>`

                : '-';



            return `

            <tr>

                <td style="color:var(--text-muted)">${globalIdx}</td>

                <td>

                    <div style="font-weight:600; font-size:.9rem">

                        ${escapeHtml(sub.original_filename || sub.filename)}

                    </div>

                    ${sub.description

                        ? `<div style="font-size:.8rem; color:var(--text-muted)">

                               ${escapeHtml(sub.description)}

                           </div>`

                        : ''}

                </td>

                <td>${rmseDisplay}</td>

                <td>${statusBadge}</td>

                <td style="color:var(--text-muted); font-size:.85rem">

                    ${formatDate(sub.submitted_at)}

                </td>

                <td>${selectBtn}</td>

            </tr>`;

        }).join('');



        // 페이지네이션

        renderPagination(

            'my-submissions-pagination',

            page,

            pages,

            loadMySubmissions

        );



    } catch (err) {

        tbody.innerHTML = `

            <tr>

                <td colspan="6" class="loading-cell">

                    서버 연결에 실패했습니다.

                </td>

            </tr>`;

    }

}



/* =============================================

   최종 제출 선택

   ============================================= */

async function selectSubmission(submissionId) {

    try {

        const data = await apiFetch(

            `/submissions/${submissionId}/select`,

            { method: 'POST' }

        );



        if (!data || !data.success) {

            showToast(data?.message || '선택에 실패했습니다.', 'error');

            return;

        }



        showToast('최종 제출이 선택되었습니다.', 'success');

        loadMySubmissions(state.mySubsPage);



    } catch (err) {

        showToast('서버 연결에 실패했습니다.', 'error');

    }

}



/* =============================================

   페이지네이션 렌더링

   ============================================= */

function renderPagination(containerId, currentPage, totalPages, callback) {

    const container = document.getElementById(containerId);



    if (totalPages <= 1) {

        container.innerHTML = '';

        return;

    }



    let html = '';



    // 이전 버튼

    html += `

        <button

            class="page-btn"

            onclick="${callback.name}(${currentPage - 1})"

            ${currentPage === 1 ? 'disabled' : ''}

        >

            <i class="fas fa-chevron-left"></i>

        </button>`;



    // 페이지 번호

    const startPage = Math.max(1, currentPage - 2);

    const endPage   = Math.min(totalPages, currentPage + 2);



    if (startPage > 1) {

        html += `<button class="page-btn" onclick="${callback.name}(1)">1</button>`;

        if (startPage > 2) {

            html += `<span style="padding:0 4px;color:var(--text-muted)">...</span>`;

        }

    }



    for (let p = startPage; p <= endPage; p++) {

        html += `

            <button

                class="page-btn ${p === currentPage ? 'active' : ''}"

                onclick="${callback.name}(${p})"

            >

                ${p}

            </button>`;

    }



    if (endPage < totalPages) {

        if (endPage < totalPages - 1) {

            html += `<span style="padding:0 4px;color:var(--text-muted)">...</span>`;

        }

        html += `

            <button

                class="page-btn"

                onclick="${callback.name}(${totalPages})"

            >

                ${totalPages}

            </button>`;

    }



    // 다음 버튼

    html += `

        <button

            class="page-btn"

            onclick="${callback.name}(${currentPage + 1})"

            ${currentPage === totalPages ? 'disabled' : ''}

        >

            <i class="fas fa-chevron-right"></i>

        </button>`;



    container.innerHTML = html;

}



/* =============================================

   모달 제어

   ============================================= */

function openModal(modalId) {

    document.getElementById(modalId).classList.remove('hidden');

    document.body.style.overflow = 'hidden';

}



function closeModal(modalId) {

    document.getElementById(modalId).classList.add('hidden');

    document.body.style.overflow = '';



    // 에러 메시지 초기화

    const errorEls = document.querySelectorAll(`#${modalId} .alert-danger`);

    errorEls.forEach(el => {

        el.classList.add('hidden');

        el.textContent = '';

    });

}



function switchModal(fromId, toId) {

    closeModal(fromId);

    openModal(toId);

}



function openScoringModal(submissionId) {

    document.getElementById('scoring-progress').style.width = '0%';

    document.getElementById('scoring-status').textContent   = '파일 검증 중...';

    openModal('scoring-modal');



    const steps = [

        { msg: '파일 검증 중...',      pct: 20  },

        { msg: 'RMSE 계산 중...',      pct: 50  },

        { msg: '리더보드 업데이트...', pct: 80  },

        { msg: '완료!',                pct: 100 },

    ];



    let stepIdx  = 0;

    const animTimer = setInterval(() => {

        if (stepIdx < steps.length) {

            document.getElementById('scoring-progress').style.width =

                `${steps[stepIdx].pct}%`;

            document.getElementById('scoring-status').textContent =

                steps[stepIdx].msg;

            stepIdx++;

        } else {

            clearInterval(animTimer);

        }

    }, 800);



    // 폴링

    let pollCount      = 0;

    state.pollingTimer = setInterval(async () => {

        pollCount++;



        if (pollCount > 30) {

            clearInterval(state.pollingTimer);

            clearInterval(animTimer);

            closeModal('scoring-modal');

            showToast(

                '채점 시간이 초과되었습니다. 잠시 후 확인해주세요.',

                'warning'

            );

            return;

        }



        try {

            const data = await apiFetch(

                `/submissions/${submissionId}/status`

            );

            if (!data || !data.success) return;



            const { status, public_rmse, error } = data.data;



            if (status === 'completed') {

                clearInterval(state.pollingTimer);

                clearInterval(animTimer);

                closeModal('scoring-modal');

                showSubmitResult(public_rmse);

                loadLeaderboard();

                loadMyRank();

                loadMySubmissions();

                showToast(

                    `채점 완료! Public RMSE: ${public_rmse.toFixed(4)}`,

                    'success'

                );



            } else if (status === 'failed') {

                clearInterval(state.pollingTimer);

                clearInterval(animTimer);

                closeModal('scoring-modal');

                showToast(

                    `채점 실패: ${error || '알 수 없는 오류'}`,

                    'error'

                );

                loadMySubmissions();

            }



        } catch (err) {

            console.error('폴링 오류:', err);

        }

    }, 2000);

}



/* =============================================

   토스트 알림

   ============================================= */

function showToast(message, type = 'info') {

    const iconMap = {

        success: 'fa-check-circle',

        error:   'fa-times-circle',

        warning: 'fa-exclamation-triangle',

        info:    'fa-info-circle',

    };



    const toast = document.createElement('div');

    toast.className = `toast ${type}`;

    toast.innerHTML = `

        <i class="fas ${iconMap[type] || iconMap.info} ${type}"></i>

        <span>${escapeHtml(message)}</span>

    `;



    document.getElementById('toast-container').appendChild(toast);



    // 3초 후 자동 제거

    setTimeout(() => {

        toast.style.opacity   = '0';

        toast.style.transform = 'translateX(20px)';

        toast.style.transition = 'all .3s ease';

        setTimeout(() => toast.remove(), 300);

    }, 3000);

}



/* =============================================

   유틸리티 함수

   ============================================= */

function show(id) {

    document.getElementById(id)?.classList.remove('hidden');

}



function hide(id) {

    document.getElementById(id)?.classList.add('hidden');

}



function showError(elementId, message) {

    const el = document.getElementById(elementId);

    if (!el) return;

    el.textContent = message;

    el.classList.remove('hidden');

}



function escapeHtml(str) {

    if (!str) return '';

    return String(str)

        .replace(/&/g,  '&amp;')

        .replace(/</g,  '&lt;')

        .replace(/>/g,  '&gt;')

        .replace(/"/g,  '&quot;')

        .replace(/'/g,  '&#039;');

}



function formatDate(isoString) {

    if (!isoString) return '-';

    const d = new Date(isoString);

    return d.toLocaleString('ko-KR', {

        year:   '2-digit',

        month:  '2-digit',

        day:    '2-digit',

        hour:   '2-digit',

        minute: '2-digit',

    });

}



function getRankIcon(rank) {

    if (rank === 1) return '🥇';

    if (rank === 2) return '🥈';

    if (rank === 3) return '🥉';

    return `${rank}`;

}



function getRankClass(rank) {

    if (rank === 1) return 'rank-1';

    if (rank === 2) return 'rank-2';

    if (rank === 3) return 'rank-3';

    return '';

}



function getStatusBadge(status) {

       const map = {

        completed:  { label: '완료',     cls: 'status-completed', icon: 'fa-check-circle'   },

        pending:    { label: '대기 중',  cls: 'status-pending',   icon: 'fa-clock'           },

        processing: { label: '채점 중',  cls: 'status-processing', icon: 'fa-spinner fa-spin'},

        failed:     { label: '실패',     cls: 'status-failed',    icon: 'fa-times-circle'    },

    };



    const s = map[status] || map.pending;

    return `

        <span class="status-badge ${s.cls}">

            <i class="fas ${s.icon}"></i>

            ${s.label}

        </span>`;

}



/* =============================================

   키보드 이벤트 (ESC → 모달 닫기)

   ============================================= */

document.addEventListener('keydown', e => {

    if (e.key !== 'Escape') return;

    ['login-modal', 'register-modal'].forEach(id => {

        if (!document.getElementById(id).classList.contains('hidden')) {

            closeModal(id);

        }

    });

});