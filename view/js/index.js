// Configuration
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
// Standard token key aligned with backend naming
const TOKEN_KEY = 'access_token';
// Legacy key for migration support
const LEGACY_TOKEN_KEY = 'auth_token';

// NEW (replaced previous enhanced loader): Configurable layout loader
async function loadLayout() {
    // Allow pages to define window.__LAYOUT_PATHS__ before this script loads
    const candidates = (window.__LAYOUT_PATHS__ && Array.isArray(window.__LAYOUT_PATHS__))
        ? window.__LAYOUT_PATHS__
        : [
            'user/partials/layout.html',          // likely absolute (if mounted under /user)
            'view/user/partials/layout.html',     // if served with /view prefix
            'static/user/partials/layout.html',   // if static mounted under /static
            '/view/user/partials/layout.html',    // absolute variant
            '/static/user/partials/layout.html'   // absolute static
          ];

    let loadedFrom = null, html = null, failures = [];
    for (const path of candidates) {
        try {
            const res = await fetch(path, { cache: 'no-cache' });
            if (res.ok) {
                html = await res.text();
                loadedFrom = path;
                break;
            } else {
                failures.push(`${path} (${res.status})`);
            }
        } catch (e) {
            failures.push(`${path} (error)`);
        }
    }

    const navPlaceholder = document.getElementById('navbarContainer');
    const footerPlaceholder = document.getElementById('footerContainer');

    if (html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const nav = temp.querySelector('nav[data-role="main-nav"]');
        const footer = temp.querySelector('footer[data-role="main-footer"]');
        if (nav && navPlaceholder) navPlaceholder.replaceWith(nav);
        if (footer && footerPlaceholder) footerPlaceholder.replaceWith(footer);
        console.log('[layout] Loaded:', loadedFrom);
    } else {
        console.warn('[layout] All attempts failed. Tried:', failures.join(', '));
        if (navPlaceholder) {
            navPlaceholder.outerHTML = `
                <nav data-role="main-nav" class="bg-white border-b border-light px-4 py-3 flex justify-between items-center">
                    <a href="/home" class="text-lg font-bold gradient-text">UniRecommend</a>
                    <div class="flex items-center gap-4">
                        <span id="tokenStatus" class="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">...</span>
                        <button onclick="logout()" class="text-xs text-red-500 font-medium hover:text-red-600">Logout</button>
                    </div>
                </nav>`;
        }
        if (footerPlaceholder) {
            footerPlaceholder.outerHTML = `
                <footer data-role="main-footer" class="bg-white border-t border-light text-center text-xs text-gray-500 py-6">
                    <div>&copy; ${new Date().getFullYear()} UniRecommend</div>
                </footer>`;
        }
    }

    updateTokenDisplay();
    initLayoutInteractive(); // added
}

// Added: initialize navbar/footer dynamic behaviors
function initLayoutInteractive() {
    const yearSpan = document.getElementById('year');
    if (yearSpan) yearSpan.textContent = new Date().getFullYear();
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileBtn && mobileMenu && !mobileBtn.dataset.bound) {
        mobileBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));
        mobileBtn.dataset.bound = '1';
    }
    // Newsletter form
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm && !newsletterForm.dataset.bound) {
        const msg = document.getElementById('newsletterMessage');
        newsletterForm.addEventListener('submit', e => {
            e.preventDefault();
            const email = new FormData(newsletterForm).get('email');
            if (msg) {
                msg.textContent = 'Subscribed: ' + email + ' (demo only)';
                msg.classList.remove('text-red-400');
            }
            newsletterForm.reset();
        });
        newsletterForm.dataset.bound = '1';
    }
}

// Utility Functions
function getToken() {
    const current = localStorage.getItem(TOKEN_KEY);
    if (current) return current;
    const legacy = localStorage.getItem(LEGACY_TOKEN_KEY);
    if (legacy) {
        localStorage.setItem(TOKEN_KEY, legacy);
        localStorage.removeItem(LEGACY_TOKEN_KEY);
        return legacy;
    }
    return null;
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(LEGACY_TOKEN_KEY, token); // temporary dual write
    updateTokenDisplay();
    updateAuthNav();
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    updateTokenDisplay();
    updateAuthNav();
}

function updateTokenDisplay() {
    const token = getToken();
    const tokenDisplays = document.querySelectorAll('#tokenDisplay');
    const tokenStatus = document.getElementById('tokenStatus');
    
    tokenDisplays.forEach(display => {
        if (token) {
            // Show truncated token
            const truncated = token.substring(0, 50) + '...';
            display.textContent = truncated;
        } else {
            display.textContent = 'No token stored';
        }
    });
    
    if (tokenStatus) {
        if (token) {
            tokenStatus.textContent = 'Authenticated';
            tokenStatus.className = 'px-3 py-2 rounded-lg text-sm font-medium bg-green-100 text-green-800';
        } else {
            tokenStatus.textContent = 'Not authenticated';
            tokenStatus.className = 'px-3 py-2 rounded-lg text-sm font-medium bg-red-100 text-red-800';
        }
    }
}

// ---------------------------------------------------------------------------
// Navbar authentication state handling (fix nav auth condition)
// ---------------------------------------------------------------------------
async function updateAuthNav() {
    const token = getToken();
    const unauth = document.getElementById('unauthenticated-nav');
    const auth = document.getElementById('authenticated-nav');
    const mUnauth = document.getElementById('mobile-unauthenticated');
    const mAuth = document.getElementById('mobile-authenticated');
    const container = document.getElementById('auth-section');

    if (!unauth && !auth && !mUnauth && !mAuth) return; // layout not injected yet
    if (container) container.classList.remove('hidden');

    const showUnauth = () => {
        unauth && unauth.classList.remove('hidden');
        auth && auth.classList.add('hidden');
        mUnauth && mUnauth.classList.remove('hidden');
        mAuth && mAuth.classList.add('hidden');
    };
    const showAuth = () => {
        unauth && unauth.classList.add('hidden');
        auth && auth.classList.remove('hidden');
        mUnauth && mUnauth.classList.add('hidden');
        mAuth && mAuth.classList.remove('hidden');
    };

    if (!token) { showUnauth(); return; }

    try {
        const res = await fetch(`${API_BASE_URL}/auth/verify`, { headers: { 'Authorization': `Bearer ${token}` }});
        if (!res.ok) throw new Error('invalid');
        showAuth();
    } catch (e) {
        console.warn('[auth-nav] token invalid, clearing');
        clearToken();
        showUnauth();
    }
}

function bindAuthNavEvents() {
    const logoutBtn = document.getElementById('logout-btn');
    const mobileLogoutBtn = document.getElementById('mobile-logout-btn');
    if (logoutBtn && !logoutBtn.dataset.bound) { logoutBtn.addEventListener('click', () => logout()); logoutBtn.dataset.bound='1'; }
    if (mobileLogoutBtn && !mobileLogoutBtn.dataset.bound) { mobileLogoutBtn.addEventListener('click', () => logout()); mobileLogoutBtn.dataset.bound='1'; }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    
    if (successDiv) successDiv.classList.add('hidden');
    if (errorDiv) {
        const messageSpan = errorDiv.querySelector('span');
        if (messageSpan) {
            messageSpan.textContent = message;
        } else {
            errorDiv.innerHTML = `
                <div class="flex">
                    <svg class="w-5 h-5 text-red-400 mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                    <span class="text-red-700 text-sm font-medium">${message}</span>
                </div>
            `;
        }
        errorDiv.classList.remove('hidden');
    }
    
    console.error('Error:', message);
}

function showSuccess(message) {
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    
    if (errorDiv) errorDiv.classList.add('hidden');
    if (successDiv) {
        const messageSpan = successDiv.querySelector('span');
        if (messageSpan) {
            messageSpan.textContent = message;
        } else {
            successDiv.innerHTML = `
                <div class="flex">
                    <svg class="w-5 h-5 text-green-400 mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                    <span class="text-green-700 text-sm font-medium">${message}</span>
                </div>
            `;
        }
        successDiv.classList.remove('hidden');
    }
    
    console.log('Success:', message);
}

function updateApiResponse(response) {
    const apiResponse = document.getElementById('apiResponse');
    if (apiResponse) {
        apiResponse.textContent = JSON.stringify(response, null, 2);
    }
}

// API Functions
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = getToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    
    if (token) {
        defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        console.log(`Making API call to: ${url}`, finalOptions);
        const response = await fetch(url, finalOptions);
        
        // Get content type to handle different response types
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            data = { error: text || 'Unknown error' };
        }
        
        console.log('API Response:', { 
            status: response.status, 
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            data 
        });
        updateApiResponse({ status: response.status, data });
        
        if (!response.ok) {
            // Handle different error response formats
            let errorMessage = 'Unknown error occurred';
            
            if (data.detail) {
                if (Array.isArray(data.detail)) {
                    // Validation errors (422)
                    errorMessage = data.detail.map(err => 
                        `${err.loc ? err.loc.join('.') : 'field'}: ${err.msg}`
                    ).join(', ');
                } else if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else {
                    errorMessage = JSON.stringify(data.detail);
                }
            } else if (data.message) {
                errorMessage = data.message;
            } else if (data.error) {
                errorMessage = data.error;
            } else {
                errorMessage = `HTTP ${response.status} ${response.statusText}`;
            }
            
            console.error('API Error Details:', {
                status: response.status,
                statusText: response.statusText,
                data,
                errorMessage
            });
            
            throw new Error(errorMessage);
        }
        
        return data;
    } catch (error) {
        // If it's already our custom error, re-throw it
        if (error.message && !error.message.includes('Failed to fetch')) {
            throw error;
        }
        
        // Handle network errors
        console.error('API call failed:', error);
        const networkError = new Error(`Network error: ${error.message}`);
        updateApiResponse({ error: networkError.message });
        throw networkError;
    }
}

// Authentication Functions
async function login(email, password) {
    try {
        const response = await apiCall('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (response.access_token) {
            setToken(response.access_token);
            showSuccess(`Login successful! Welcome ${response.email}`);
            return response;
        } else {
            throw new Error('No access token received');
        }
    } catch (error) {
        showError(`Login failed: ${error.message}`);
        throw error;
    }
}

async function testLogin() {
    // Show prompt for test credentials since we don't want to hardcode them
    const testEmail = prompt('Enter test email:', 'minkhantthwin17@gmail.com');
    const testPassword = prompt('Enter test password:');
    
    if (!testEmail || !testPassword) {
        showError('Test login cancelled');
        return;
    }
    
    try {
        await login(testEmail, testPassword);
    } catch (error) {
        showError(`Test login failed: ${error.message}. Please make sure the user exists and the password is correct.`);
    }
}

async function logout() {
    try {
        const token = getToken();
        if (token) {
            await apiCall('/auth/logout', { method: 'POST' });
        }
        
        clearToken();
        showSuccess('Logged out successfully');
        
        // Redirect to login page if we're on the dashboard
        if (window.location.pathname.includes('/home')) {
            window.location.href = '/login';
        }
    } catch (error) {
        // Even if the API call fails, clear the local token
        clearToken();
        showError(`Logout warning: ${error.message}`);
        
        if (window.location.pathname.includes('/home')) {
            window.location.href = '/login';
        }
    }
}

async function testTokenVerify() {
    try {
        const response = await apiCall('/auth/verify');
        showSuccess('Token is valid!');
        return response;
    } catch (error) {
        showError(`Token verification failed: ${error.message}`);
        throw error;
    }
}

async function testRefreshToken() {
    try {
        const response = await apiCall('/auth/refresh', { method: 'POST' });
        
        if (response.access_token) {
            setToken(response.access_token);
            showSuccess('Token refreshed successfully!');
        }
        
        return response;
    } catch (error) {
        showError(`Token refresh failed: ${error.message}`);
        throw error;
    }
}

async function testAuthMe() {
    try {
        const response = await apiCall('/auth/me');
        showSuccess('Successfully retrieved user information!');
        return response;
    } catch (error) {
        showError(`Failed to get user info: ${error.message}`);
        throw error;
    }
}

async function testAuthVerify() {
    try {
        const response = await apiCall('/auth/verify');
        showSuccess('Token verification successful!');
        return response;
    } catch (error) {
        showError(`Token verification failed: ${error.message}`);
        throw error;
    }
}

// User Profile Functions
async function loadUserProfile() {
    try {
        const profileDiv = document.getElementById('userProfile');
        if (profileDiv) {
            profileDiv.innerHTML = `
                <div class="flex items-center justify-center py-12">
                    <div class="animate-pulse flex space-x-4">
                        <div class="rounded-full bg-gray-300 h-12 w-12"></div>
                        <div class="flex-1 space-y-2">
                            <div class="h-4 bg-gray-300 rounded w-3/4"></div>
                            <div class="h-4 bg-gray-300 rounded w-1/2"></div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        const response = await apiCall('/auth/me');
        
        if (profileDiv) {
            profileDiv.innerHTML = `
                <div class="space-y-6">
                    <div class="flex items-center space-x-4">
                        <div class="w-16 h-16 bg-gradient-to-r from-primary to-accent rounded-full flex items-center justify-center">
                            <span class="text-white text-xl font-bold">
                                ${(response.first_name || 'U').charAt(0)}${(response.last_name || '').charAt(0)}
                            </span>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-900">
                                ${response.first_name || 'N/A'} ${response.last_name || 'N/A'}
                            </h3>
                            <p class="text-gray-600">${response.email}</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <div class="text-sm font-medium text-gray-500 mb-1">Phone</div>
                            <div class="text-gray-900">${response.phone || 'Not provided'}</div>
                        </div>
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <div class="text-sm font-medium text-gray-500 mb-1">Date of Birth</div>
                            <div class="text-gray-900">${response.date_of_birth || 'Not provided'}</div>
                        </div>
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <div class="text-sm font-medium text-gray-500 mb-1">Nationality</div>
                            <div class="text-gray-900">${response.nationality || 'Not provided'}</div>
                        </div>
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <div class="text-sm font-medium text-gray-500 mb-1">Member Since</div>
                            <div class="text-gray-900">${new Date(response.created_at).toLocaleDateString()}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Update user email in header and initials
        const userEmailSpan = document.getElementById('userEmail');
        const userInitials = document.getElementById('userInitials');
        if (userEmailSpan) {
            userEmailSpan.textContent = response.email;
        }
        if (userInitials) {
            userInitials.textContent = `${(response.first_name || 'U').charAt(0)}${(response.last_name || '').charAt(0)}`;
        }
        
        return response;
    } catch (error) {
        const profileDiv = document.getElementById('userProfile');
        if (profileDiv) {
            profileDiv.innerHTML = `
                <div class="text-center py-12">
                    <svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <p class="text-red-600">Failed to load profile: ${error.message}</p>
                </div>
            `;
        }
        showError(`Failed to load profile: ${error.message}`);
        throw error;
    }
}

async function loadRecommendations() {
    try {
        const recommendationsDiv = document.getElementById('recommendationsContent');
        if (recommendationsDiv) {
            recommendationsDiv.innerHTML = `
                <div class="flex items-center justify-center py-12">
                    <div class="text-center">
                        <svg class="animate-spin w-8 h-8 text-primary mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <p class="text-gray-600">Loading your personalized recommendations...</p>
                    </div>
                </div>
            `;
        }

        // Get current user
        const userResponse = await apiCall('/auth/me');
        const userId = userResponse.id;

        // Fetch new recommendation API (returns object)
        const apiData = await apiCall(`/users/${userId}/recommendations?limit=50`);
        const allRecs = (apiData && Array.isArray(apiData.recommendations)) ? apiData.recommendations : [];

        // Normalize score field: backend uses final_score (0-100). Filter out < 50.
        const processed = allRecs
            .map(r => ({
                ...r,
                final_score: typeof r.final_score === 'number' ? r.final_score : (typeof r.score === 'number' ? r.score : 0)
            }))
            .filter(r => r.final_score >= 50)
            .sort((a,b) => b.final_score - a.final_score);

        if (recommendationsDiv) {
            if (processed.length > 0) {
                const metaBadges = apiData?.recommendation_sources ? `
                    <div class="flex flex-wrap gap-2 justify-center mb-4">
                        <span class="px-2 py-1 bg-primary bg-opacity-10 text-primary rounded text-xs">Interest: ${apiData.recommendation_sources.interest_based || apiData.recommendation_sources.interest_based_count || 0}</span>
                        <span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Qualification: ${apiData.recommendation_sources.qualification_based || apiData.recommendation_sources.qualification_based_count || 0}</span>
                        <span class="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs">Test Score: ${apiData.recommendation_sources.test_score_based || apiData.recommendation_sources.test_score_based_count || 0}</span>
                        <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">Shown: ${processed.length}</span>
                    </div>` : '';

                const recommendationsHtml = processed.map((rec, index) => {
                    const pct = rec.final_score ?? 0;
                    const badge = pct >= 85 ? '<span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">Top Match</span>' : pct >= 70 ? '<span class="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">Strong Match</span>' : '<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">Match</span>';
                    const reasons = rec.match_reasons || rec.factors || [];
                    const reasonHtml = reasons.length ? `<ul class="list-disc pl-5 space-y-1 text-gray-600">${reasons.slice(0,5).map(r=>`<li>${r}</li>`).join('')}</ul>` : `<p class="text-gray-600">${rec.reason || 'Based on your profile and preferences.'}</p>`;
                    return `
                    <div class="bg-gradient-to-r from-light-blue to-lighter-blue border border-gray-border rounded-xl p-6 hover:shadow-lg transition-all duration-200">
                        <div class="flex items-start justify-between mb-4">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-gradient-to-r from-primary to-accent rounded-lg flex items-center justify-center text-white font-bold text-sm">${index + 1}</div>
                                <div>
                                    <h4 class="text-lg font-semibold text-gray-900">${rec.program_name || rec.name || 'Unknown Program'}</h4>
                                    <p class="text-gray-600">${rec.university_name || rec.university || 'Unknown University'}</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-2xl font-bold text-primary">${pct.toFixed(1)}</div>
                                <div class="text-sm text-gray-500">Final Score</div>
                            </div>
                        </div>
                        <div class="bg-white rounded-lg p-4">
                            <div class="text-sm font-medium text-gray-700 mb-2">Why this is a good match:</div>
                            ${reasonHtml}
                        </div>
                        <div class="flex justify-between items-center mt-4">
                            <div class="flex flex-wrap gap-2">${badge}</div>
                            <button class="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors font-medium" data-program-id="${rec.program_id || rec.id || ''}">Learn More</button>
                        </div>
                        <div class="mt-4">
                            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                <div class="h-2 bg-gradient-to-r from-primary to-accent" style="width:${Math.min(100, pct)}%"></div>
                            </div>
                        </div>
                    </div>`;
                }).join('');

                recommendationsDiv.innerHTML = `
                    <div class="space-y-6">
                        <div class="text-center mb-2">
                            <h3 class="text-xl font-semibold text-gray-900 mb-2">Your Personalized Recommendations</h3>
                            <p class="text-gray-600 mb-2">Filtered to show programs with final score ≥ 50.</p>
                            ${metaBadges}
                        </div>
                        <div class="space-y-4">${recommendationsHtml}</div>
                    </div>`;
            } else {
                recommendationsDiv.innerHTML = `
                    <div class="text-center py-12">
                        <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                        </svg>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">No High-Score Recommendations</h3>
                        <p class="text-gray-500">We didn't find programs with a final score ≥ 50. Add more interests, test scores, or qualifications to improve matches.</p>
                    </div>`;
            }
        }

        return processed;
    } catch (error) {
        const recommendationsDiv = document.getElementById('recommendationsContent');
        if (recommendationsDiv) {
            recommendationsDiv.innerHTML = `
                <div class="text-center py-12">
                    <svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <p class="text-red-600">Failed to load recommendations: ${error.message}</p>
                </div>`;
        }
        showError(`Failed to load recommendations: ${error.message}`);
        throw error;
    }
}

async function testUserRecommendations() {
    try {
        await loadRecommendations();
        showSuccess('Recommendations loaded successfully!');
    } catch (error) {
        showError(`Failed to load recommendations: ${error.message}`);
    }
}

// Token Management Functions
function showToken() {
    const token = getToken();
    const modal = document.getElementById('tokenModal');
    const tokenTextarea = document.getElementById('fullToken');
    
    if (token && modal && tokenTextarea) {
        tokenTextarea.value = token;
        modal.classList.remove('hidden');
    } else {
        showError('No token to display');
    }
}

function closeModal() {
    const modal = document.getElementById('tokenModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function copyToken() {
    const tokenTextarea = document.getElementById('fullToken');
    if (tokenTextarea) {
        tokenTextarea.select();
        document.execCommand('copy');
        showSuccess('Token copied to clipboard!');
    }
}

function clearStorage() {
    clearToken();
    showSuccess('Local storage cleared!');
}

// State for modal-collected data (moved near top for safety)
const collectedInterests = [];
const collectedTestScores = [];

function renderInterests() {
    const container = document.getElementById('interestsContainer');
    if (!container) return;
    container.innerHTML = '';
    if (collectedInterests.length === 0) {
        container.innerHTML = '<div id="noInterests" class="text-sm text-gray-500 italic">No interests added yet.</div>';
        return;
    }
    collectedInterests.forEach((item, idx) => {
        const div = document.createElement('div');
        div.className = 'flex items-start justify-between bg-gray-50 p-4 rounded-lg border border-gray-border';
        div.innerHTML = `
            <div>
                <div class="font-medium text-gray-900">${item.field_of_study}</div>
                <div class="text-xs text-gray-500 capitalize">Level: ${item.interest_level}</div>
            </div>
            <button type="button" class="text-red-500 hover:text-red-600 text-sm font-medium" data-remove-interest="${idx}">Remove</button>
        `;
        container.appendChild(div);
    });
    container.querySelectorAll('[data-remove-interest]').forEach(btn => {
        btn.addEventListener('click', () => {
            const index = parseInt(btn.getAttribute('data-remove-interest'), 10);
            collectedInterests.splice(index, 1);
            renderInterests();
        });
    });
}

function renderTestScores() {
    const container = document.getElementById('testScoresContainer');
    if (!container) return;
    container.innerHTML = '';
    if (collectedTestScores.length === 0) {
        container.innerHTML = '<div id="noTestScores" class="text-sm text-gray-500 italic">No test scores added yet.</div>';
        return;
    }
    collectedTestScores.forEach((item, idx) => {
        const div = document.createElement('div');
        div.className = 'bg-gray-50 p-4 rounded-lg border border-gray-border';
        div.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-6 gap-2 text-sm">
                <div><span class="font-medium">Test:</span> ${item.test_type}</div>
                <div><span class="font-medium">Score:</span> ${item.score}${item.max_score ? '/' + item.max_score : ''}</div>
                <div><span class="font-medium">Test Date:</span> ${item.test_date || '—'}</div>
                <div><span class="font-medium">Expiry Date:</span> ${item.expiry_date || '—'}</div>
                <div class="md:col-span-2 flex justify-end">
                    <button type="button" class="text-red-500 hover:text-red-600 font-medium" data-remove-testscore="${idx}">Remove</button>
                </div>
            </div>`;
        container.appendChild(div);
    });
    container.querySelectorAll('[data-remove-testscore]').forEach(btn => {
        btn.addEventListener('click', () => {
            const index = parseInt(btn.getAttribute('data-remove-testscore'), 10);
            collectedTestScores.splice(index, 1);
            renderTestScores();
        });
    });
}

function openModal(el) {
    if (!el) return;
    const panel = el.querySelector('.modal-panel');
    el.classList.remove('hidden');
    requestAnimationFrame(() => {
        el.classList.remove('opacity-0');
        if (panel) {
            panel.classList.remove('opacity-0', 'scale-95');
            panel.classList.add('opacity-100', 'scale-100');
        }
    });
    document.body.classList.add('overflow-hidden');
}

function closeModal(el) {
    if (!el) return;
    const panel = el.querySelector('.modal-panel');
    el.classList.add('opacity-0');
    if (panel) {
        panel.classList.add('opacity-0', 'scale-95');
        panel.classList.remove('opacity-100', 'scale-100');
    }
    setTimeout(() => {
        el.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }, 180);
}

function setupInterestModal() {
    const openBtn = document.getElementById('openInterestModal');
    const modal = document.getElementById('interestModal');
    const closeBtn = document.getElementById('closeInterestModalBtn');
    const cancelBtn = document.getElementById('cancelInterest');
    const form = document.getElementById('interestForm');
    if (!modal || !form) { console.warn('Interest modal elements missing'); return; }
    if (openBtn) openBtn.addEventListener('click', () => { form.reset(); openModal(modal); });
    [closeBtn, cancelBtn].filter(Boolean).forEach(btn => btn.addEventListener('click', () => closeModal(modal)));
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(modal); });
    form.addEventListener('submit', e => {
        e.preventDefault();
        const field = document.getElementById('interest_field').value.trim();
        const level = document.getElementById('interest_level').value;
        if (field) {
            collectedInterests.push({ field_of_study: field, interest_level: level });
            renderInterests();
            closeModal(modal);
        }
    });
    console.log('Interest modal initialized');
}

function setupTestScoreModal() {
    const openBtn = document.getElementById('openTestScoreModal');
    const modal = document.getElementById('testScoreModal');
    const closeBtn = document.getElementById('closeTestScoreModalBtn');
    const cancelBtn = document.getElementById('cancelTestScore');
    const form = document.getElementById('testScoreForm');
    if (!modal || !form) { console.warn('Test score modal elements missing'); return; }
    if (openBtn) openBtn.addEventListener('click', () => { form.reset(); openModal(modal); });
    [closeBtn, cancelBtn].filter(Boolean).forEach(btn => btn.addEventListener('click', () => closeModal(modal)));
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(modal); });
    form.addEventListener('submit', e => {
        e.preventDefault();
        const test_type = document.getElementById('test_type').value.trim();
        const score = document.getElementById('test_score').value.trim();
        if (!test_type || !score) return;
        collectedTestScores.push({
            test_type,
            score,
            max_score: document.getElementById('test_max_score').value.trim() || null,
            test_date: document.getElementById('test_date').value || null,
            expiry_date: document.getElementById('expiry_date').value || null
        });
        renderTestScores();
        closeModal(modal);
    });
    console.log('Test score modal initialized');
}

// Page Initialization Functions
function initializeDashboard() {
    const token = getToken();
    if (!token) {
        // No token, redirect to login
        window.location.href = '/login';
        return;
    }
    
    // Update token display
    updateTokenDisplay();
    
    // Load user profile
    loadUserProfile()
        .then(user => {
            // Trigger qualification check (non-forced; respects cooldown)
            checkAllQualifications(false);
        })
        .catch(error => {
            console.error('Failed to load initial profile:', error);
            // If token is invalid, redirect to login
            if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                clearToken();
                window.location.href = '/login';
            }
        });
}

// ---------------------------------------------------------------------------
// Qualification Auto-Check
// ---------------------------------------------------------------------------
let __qualCheckInProgress = false;

async function checkAllQualifications(force = false) {
    if (__qualCheckInProgress) return;
    try {
        const user = await apiCall('/auth/me');
        const userId = user.id;
        const storageKey = `qual_check_${userId}`;
        const last = JSON.parse(localStorage.getItem(storageKey) || 'null');

        // Skip if recently checked (within 12h) unless forced
        if (!force && last && Date.now() - last.timestamp < 12 * 60 * 60 * 1000) {
            console.log('[qual-check] Recent check exists, skipping.');
            return;
        }

        __qualCheckInProgress = true;
        console.log('[qual-check] Running qualification check for user', userId);

        const results = await apiCall(`/users/${userId}/qualifications/check-all`, {
            method: 'POST'
        });

        localStorage.setItem(storageKey, JSON.stringify({
            timestamp: Date.now(),
            total: Array.isArray(results) ? results.length : 0
        }));

        console.log('[qual-check] Completed. Programs evaluated:', Array.isArray(results) ? results.length : results);
    } catch (e) {
        console.warn('[qual-check] Failed:', e.message);
    } finally {
        __qualCheckInProgress = false;
    }
}

// Expose (optional)
window.checkAllQualifications = checkAllQualifications;

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    loadLayout().finally(() => {
        // Update token display on page load
        updateTokenDisplay();
    // Ensure auth nav reflects state & events bound
    bindAuthNavEvents();
    updateAuthNav();
        
        // Login form handler
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const loginBtn = document.getElementById('loginBtn');
                const btnText = loginBtn.querySelector('.btn-text');
                const loader = loginBtn.querySelector('.loader');
                
                // Show loading state
                loginBtn.disabled = true;
                loginBtn.classList.add('loading');
                if (btnText) btnText.classList.add('hidden');
                if (loader) loader.classList.remove('hidden');
                
                try {
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    
                    await login(email, password);

                    // Run qualification check immediately after successful login
                    checkAllQualifications(true);

                    // Redirect to dashboard on successful login
                    setTimeout(() => {
                        window.location.href = '/home';
                    }, 1000);
                } catch (error) {
                    console.error('Login failed:', error);
                } finally {
                    // Reset button state
                    loginBtn.disabled = false;
                    loginBtn.classList.remove('loading');
                    if (btnText) btnText.classList.remove('hidden');
                    if (loader) loader.classList.add('hidden');
                }
            });
        }
        
        // Registration form handler
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            // Modal based collection setup
            setupInterestModal();
            setupTestScoreModal();
            // Render any existing (empty initial)
            renderInterests();
            renderTestScores();

            registerForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                const registerBtn = document.getElementById('registerBtn');
                const btnText = registerBtn.querySelector('.btn-text');
                const loader = registerBtn.querySelector('.loader');
                registerBtn.disabled = true;
                if (btnText) btnText.classList.add('hidden');
                if (loader) loader.classList.remove('hidden');

                try {
                    const password = document.getElementById('password').value;
                    const confirmPassword = document.getElementById('confirm_password').value;
                    if (password !== confirmPassword) {
                        throw new Error('Passwords do not match');
                    }

                    const interests = collectedInterests.slice();
                    const testScores = collectedTestScores.slice();

                    const payload = {
                        email: document.getElementById('email').value.trim(),
                        password,
                        first_name: document.getElementById('first_name').value.trim(),
                        last_name: document.getElementById('last_name').value.trim(),
                        phone: document.getElementById('phone').value.trim() || null,
                        date_of_birth: document.getElementById('date_of_birth').value || null,
                        nationality: document.getElementById('nationality').value.trim() || null,
                        is_admin: document.getElementById('is_admin')?.checked || false,
                        interests,
                        test_scores: testScores
                    };

                    console.log('Registration payload:', JSON.stringify(payload, null, 2));
                    console.log('Interests:', interests);
                    console.log('Test Scores:', testScores);

                    const created = await apiCall('/users', {
                        method: 'POST',
                        body: JSON.stringify(payload)
                    });

                    console.log('User created successfully:', created);
                    showSuccess('Account created! Logging you in...');

                    // Auto login
                    await login(payload.email, password);
                    setTimeout(() => { window.location.href = '/home'; }, 1000);
                } catch (error) {
                    console.error('Registration error details:', {
                        error,
                        message: error.message,
                        stack: error.stack
                    });
                    
                    // Extract more meaningful error message
                    let errorMessage = 'Registration failed';
                    if (error.message) {
                        errorMessage = error.message;
                    }
                    
                    showError(`Registration failed: ${errorMessage}`);
                } finally {
                    registerBtn.disabled = false;
                    if (btnText) btnText.classList.remove('hidden');
                    if (loader) loader.classList.add('hidden');
                }
            });
        }

        // Initialize dashboard if on home
        if (window.location.pathname.includes('/home')) {
            initializeDashboard();
        }

        // Initialize profile page
        if (window.location.pathname.startsWith('/profile')) {
            (async () => {
                const token = getToken();
                if (!token) {
                    showError('Please login to view your profile');
                    window.location.href = '/login';
                    return;
                }
                try {
                    const user = await apiCall('/auth/me');
                    populateProfile(user);
                } catch (e) {
                    showError('Failed to load profile: ' + e.message);
                }
            })();
        }
    });
});

// Delegated click handler fallback (if direct listeners failed)
document.addEventListener('click', e => {
    const openInterest = e.target.closest('#openInterestModal');
    const openTest = e.target.closest('#openTestScoreModal');
    if (openInterest) {
        const form = document.getElementById('interestForm');
        form && form.reset();
        openModal(document.getElementById('interestModal'));
    }
    if (openTest) {
        const form = document.getElementById('testScoreForm');
        form && form.reset();
        openModal(document.getElementById('testScoreModal'));
    }
});

// Expose for debugging
window.renderInterests = renderInterests;
window.renderTestScores = renderTestScores;

// Test login modal functions
function showTestLogin() {
    const modal = document.getElementById('testLoginModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function hideTestLogin() {
    const modal = document.getElementById('testLoginModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function executeTestLogin() {
    const testEmail = document.getElementById('testEmail').value;
    const testPassword = document.getElementById('testPassword').value;
    
    if (!testEmail || !testPassword) {
        showError('Please enter both email and password');
        return;
    }
    
    try {
        await login(testEmail, testPassword);
        hideTestLogin();
        // Redirect to dashboard on successful login
        setTimeout(() => {
            window.location.href = '/home';
        }, 1000);
    } catch (error) {
        showError(`Test login failed: ${error.message}`);
    }
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('tokenModal');
    if (event.target === modal) {
        closeModal();
    }
});

// Global functions for button onclick handlers
window.login = login;
window.logout = logout;
window.testLogin = testLogin;
window.testTokenVerify = testTokenVerify;
window.testRefreshToken = testRefreshToken;
window.testAuthMe = testAuthMe;
window.testAuthVerify = testAuthVerify;
window.loadUserProfile = loadUserProfile;
window.loadRecommendations = loadRecommendations;
window.testUserRecommendations = testUserRecommendations;
window.showToken = showToken;
window.closeModal = closeModal;
window.copyToken = copyToken;
window.clearStorage = clearStorage;
window.clearToken = clearToken;
window.showTestLogin = showTestLogin;
window.hideTestLogin = hideTestLogin;
window.executeTestLogin = executeTestLogin;

// ---------------- Profile Helpers -----------------
function populateProfile(user){
    // Header
    const profileName = document.getElementById('profileName');
    if (!profileName) return; // not on profile page
    const profileEmail = document.getElementById('profileEmail');
    const profileAvatar = document.getElementById('profileAvatar');
    const memberSince = document.getElementById('memberSince');
    profileName.textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email;
    if (profileEmail) profileEmail.textContent = user.email;
    if (profileAvatar) profileAvatar.textContent = ((user.first_name||'U')[0] + (user.last_name||'')[0]).toUpperCase();
    if (memberSince && user.created_at) {
        memberSince.textContent = 'Member since ' + new Date(user.created_at).toLocaleDateString(undefined,{year:'numeric',month:'long'});
    }

    // Personal details
    const map = {
        profileFirstName: user.first_name,
        profileLastName: user.last_name,
        profileEmailDetail: user.email,
        profilePhone: user.phone,
        profileDateOfBirth: user.date_of_birth ? new Date(user.date_of_birth).toLocaleDateString() : null,
        profileNationality: user.nationality
    };
    Object.entries(map).forEach(([id,val])=>{
        const el = document.getElementById(id);
        if (el) el.textContent = val || 'Not provided';
    });

    // Interests
    const interestsList = document.getElementById('interestsList');
    if (interestsList){
        const interests = user.interests || [];
        if (!interests.length){
            interestsList.innerHTML = '<div class="flex items-center justify-center py-8 text-gray-500">No interests added yet.</div>';
        } else {
            interestsList.innerHTML = interests.map(i=>`
                <div class="flex items-center justify-between p-3 bg-light-blue rounded-lg">
                  <div><span class="font-medium text-gray-900">${i.field_of_study}</span> <span class="ml-2 text-sm text-gray-600 capitalize">(${i.interest_level})</span></div>
                  <button class="text-red-500 text-sm" disabled title="Removal not implemented">Remove</button>
                </div>`).join('');
        }
    }

    // Test scores
    const testScoresList = document.getElementById('testScoresList');
    if (testScoresList){
        const scores = user.test_scores || [];
        if (!scores.length){
            testScoresList.innerHTML = '<div class="flex items-center justify-center py-8 text-gray-500">No test scores added yet.</div>';
        } else {
            testScoresList.innerHTML = scores.map(s=>`
             <div class="flex items-center justify-between p-4 border border-gray-border rounded-lg">
               <div>
                 <div class="font-medium text-gray-900">${s.test_type}</div>
                 <div class="text-sm text-gray-600">Score: ${s.score}${s.max_score?'/'+s.max_score:''}${s.test_date? ' • Taken: '+ new Date(s.test_date).toLocaleDateString(): ''}</div>
                 ${s.expiry_date? `<div class="text-xs text-gray-500">Expires: ${new Date(s.expiry_date).toLocaleDateString()}</div>`:''}
               </div>
               <button class="text-red-500 text-sm" disabled title="Removal not implemented">Remove</button>
             </div>`).join('');
        }
    }

    // Qualifications
    const qualificationsList = document.getElementById('qualificationsList');
    if (qualificationsList){
        const quals = user.qualifications || [];
        if (!quals.length){
            qualificationsList.innerHTML = '<div class="flex items-center justify-center py-8 text-gray-500">No qualifications added yet.</div>';
        } else {
            qualificationsList.innerHTML = quals.map(q=>`
             <div class="flex items-center justify-between p-4 border border-gray-border rounded-lg">
               <div>
                 <div class="font-medium text-gray-900">${q.degree_name || q.qualification_type}</div>
                 <div class="text-sm text-gray-600">${q.institution_name || ''}${q.field_of_study? ' • '+q.field_of_study:''}</div>
                 <div class="text-xs text-gray-500">${q.grade_point? 'GPA: '+q.grade_point+(q.max_grade_point?'/'+q.max_grade_point:''):''}${q.completion_year? ' • '+q.completion_year:''}${q.country? ' • '+q.country:''}</div>
               </div>
               <button class="text-red-500 text-sm" disabled title="Removal not implemented">Remove</button>
             </div>`).join('');
        }
    }

    // Completion calculation
    computeProfileCompletion(user);
}

function computeProfileCompletion(user){
    const completionBar = document.getElementById('completionBar');
    if (!completionBar) return; // not on profile
    let score=0;
    if (user.first_name) score+=5;
    if (user.last_name) score+=5;
    if (user.email) score+=5;
    if (user.phone) score+=10;
    if (user.date_of_birth) score+=10;
    if (user.nationality) score+=5;
    if (user.interests?.length) score+= Math.min(20, user.interests.length*5);
    if (user.test_scores?.length) score+= Math.min(20, user.test_scores.length*10);
    if (user.qualifications?.length) score+= Math.min(20, user.qualifications.length*10);
    const pct = Math.min(100, Math.round(score));
    document.getElementById('completionPercentage').textContent = pct + '%';
    completionBar.style.width = pct + '%';
    const tips = [];
    if (!user.phone) tips.push('Add your phone number');
    if (!user.date_of_birth) tips.push('Add your date of birth');
    if (!user.nationality) tips.push('Add your nationality');
    if (!user.interests?.length) tips.push('Add your academic interests');
    if (!user.test_scores?.length) tips.push('Add your test scores');
    if (!user.qualifications?.length) tips.push('Add your qualifications');
    const tipsContainer = document.getElementById('completionTips');
    if (tipsContainer){
        tipsContainer.innerHTML = tips.length? tips.slice(0,3).map(t=>`<div class="flex items-center space-x-2"><div class="w-1.5 h-1.5 bg-accent rounded-full"></div><span>${t}</span></div>`).join('') : '<span class="text-green-600">Profile complete!</span>';
    }
}

// ---------------- Dynamic Quick Actions -----------------
async function initQuickActions(){
    const recBtn = document.getElementById('getRecommendationsBtn');
    const appsBtn = document.getElementById('viewApplicationsBtn');
    const searchBtn = document.getElementById('searchProgramsBtn');
    const content = document.getElementById('quickActionsContent');
    if(!recBtn || !appsBtn || !content) return; // not on a page with quick actions

    let cached = { recs: [], apps: [] };
    let state = { open: null };

    async function refreshCounts(){
        try {
            const me = await apiCall('/auth/me');
            const uid = me.id;
            const recResp = await apiCall(`/users/${uid}/recommendations?limit=30`);
            const recommendations = Array.isArray(recResp.recommendations)? recResp.recommendations: [];
            const filtered = recommendations.filter(r=> (r.final_score ?? r.score ?? 0) >= 50);
            cached.recs = filtered.sort((a,b)=>(b.final_score||b.score||0)-(a.final_score||a.score||0));

            // Attempt to fetch applications (if endpoint exists)
            let apps = [];
            try {
                const appsResp = await apiCall(`/applications?user_id=${uid}`);
                apps = Array.isArray(appsResp)? appsResp: (appsResp.items||[]);
            } catch(e){
                console.warn('[quick-actions] applications fetch failed:', e.message);
            }
            cached.apps = apps;

            const recLabel = document.getElementById('recBtnLabel');
            const appsLabel = document.getElementById('appsBtnLabel');
            if (recLabel) recLabel.textContent = `Recommendations (${cached.recs.length})`;
            if (appsLabel) appsLabel.textContent = `View Applications (${cached.apps.length})`;
            const meta = document.getElementById('quickActionsMeta');
            if (meta) {
                meta.classList.remove('hidden');
                meta.textContent = `${cached.recs.length} recs • ${cached.apps.length} apps`;
            }
        } catch(e){
            console.warn('[quick-actions] refreshCounts failed', e);
        }
    }

    function renderList(type){
        if(!content) return;
        let html='';
        if(type==='recs'){
            if(!cached.recs.length){
                html = `<div class="text-sm text-gray-500 py-4 text-center">No recommendations ≥ 50 yet. Add interests, test scores or qualifications.</div>`;
            } else {
                const items = cached.recs.slice(0,3).map(r=>{
                    const score = (r.final_score ?? r.score ?? 0).toFixed(1);
                    return `<div class="flex items-start justify-between p-3 bg-gray-50 rounded-lg mb-2">
                        <div>
                            <div class="font-medium text-gray-900 truncate max-w-[180px]">${r.program_name || r.name || 'Program'}</div>
                            <div class="text-xs text-gray-500">${r.university_name || r.university || ''}</div>
                        </div>
                        <div class="text-primary text-sm font-semibold ml-2">${score}</div>
                    </div>`;
                }).join('');
                html = `<div class="mb-3 text-sm font-medium text-gray-700">Top Matches</div>${items}<a href="/program" class="block mt-2 text-xs text-primary hover:underline">See all recommendations →</a>`;
            }
        } else if(type==='apps'){
            if(!cached.apps.length){
                html = `<div class="text-sm text-gray-500 py-4 text-center">You haven't started any applications yet.</div>`;
            } else {
                const items = cached.apps.slice(0,3).map(a=>{
                    return `<div class="flex items-start justify-between p-3 bg-gray-50 rounded-lg mb-2">
                        <div>
                            <div class="font-medium text-gray-900 truncate max-w-[180px]">${a.program_name || a.program?.name || 'Application'}</div>
                            <div class="text-xs text-gray-500 capitalize">Status: ${a.status || a.application_status || 'pending'}</div>
                        </div>
                        <span class="ml-2 text-xs px-2 py-1 rounded bg-light-blue text-primary">${a.status || a.application_status || 'pending'}</span>
                    </div>`;
                }).join('');
                html = `<div class="mb-3 text-sm font-medium text-gray-700">Recent Applications</div>${items}<a href="/application" class="block mt-2 text-xs text-primary hover:underline">Manage applications →</a>`;
            }
        }
        content.innerHTML = html;
        content.classList.remove('hidden');
    }

    function toggle(type){
        if(state.open === type){
            // close
            state.open = null;
            content.classList.add('hidden');
            content.innerHTML='';
            return;
        }
        state.open = type;
        renderList(type);
    }

    recBtn.addEventListener('click', ()=> toggle('recs'));
    appsBtn.addEventListener('click', ()=> toggle('apps'));
    if(searchBtn){
        searchBtn.addEventListener('click', ()=>{ window.location.href='/program'; });
    }

    await refreshCounts();
}

// Initialize quick actions after DOM + layout
window.addEventListener('DOMContentLoaded', ()=>{
    setTimeout(()=>{ initQuickActions(); }, 600); // slight delay to allow layout & token
});