import { onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, sendPasswordResetEmail, updateProfile } from 'firebase/auth';
import { doc, serverTimestamp, setDoc } from 'firebase/firestore';
import { auth, db, firebaseConfigured, firebaseSetupMessage } from './firebase.js';

const $ = (selector) => document.querySelector(selector);
const signInForm = $('#signInForm');
const signUpForm = $('#signUpForm');
const notice = $('#authNotice');
const setupNotice = $('#setupNotice');
const signInTab = $('#showSignInBtn');
const signUpTab = $('#showSignUpBtn');
let mode = 'signin';

function setNotice(message = '', type = '') {
  notice.textContent = message;
  notice.className = `notice auth-notice${type ? ` notice-${type}` : ''}`;
}

function setMode(nextMode) {
  mode = nextMode;
  const isSignIn = mode === 'signin';
  signInForm.hidden = !isSignIn;
  signUpForm.hidden = isSignIn;
  signInTab.classList.toggle('active', isSignIn);
  signUpTab.classList.toggle('active', !isSignIn);
  signInTab.setAttribute('aria-selected', String(isSignIn));
  signUpTab.setAttribute('aria-selected', String(!isSignIn));
  $('#authTitle').textContent = isSignIn ? 'Welcome back' : 'Create your account';
  $('#authSubtitle').textContent = isSignIn ? 'Sign in to add or update your assignment links.' : 'Create a profile so you can manage your own links.';
  setNotice('');
}

function explainAuthError(error) {
  const messages = {
    'auth/invalid-credential': 'Email or password is incorrect.',
    'auth/invalid-email': 'Please enter a valid email address.',
    'auth/email-already-in-use': 'An account with this email already exists. Please sign in instead.',
    'auth/weak-password': 'Choose a stronger password with at least 6 characters.',
    'auth/too-many-requests': 'Too many attempts. Wait a little and try again.',
    'auth/network-request-failed': 'Network error. Check your internet connection.',
    'auth/user-not-found': 'No account was found for that email address.',
    'auth/wrong-password': 'Email or password is incorrect.',
  };
  return messages[error.code] || error.message || 'Something went wrong. Please try again.';
}

signInTab.addEventListener('click', () => setMode('signin'));
signUpTab.addEventListener('click', () => setMode('signup'));

signInForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!firebaseConfigured) return setNotice(firebaseSetupMessage(), 'error');
  const email = $('#signInEmail').value.trim();
  const password = $('#signInPassword').value;
  const button = $('#signInSubmitBtn');
  button.disabled = true;
  button.textContent = 'Signing in…';
  setNotice('');
  try {
    await signInWithEmailAndPassword(auth, email, password);
    window.location.href = '/index.html?edit=1';
  } catch (error) {
    setNotice(explainAuthError(error), 'error');
  } finally {
    button.disabled = false;
    button.textContent = 'Sign in';
  }
});

signUpForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!firebaseConfigured) return setNotice(firebaseSetupMessage(), 'error');
  const name = $('#signUpName').value.trim();
  const email = $('#signUpEmail').value.trim();
  const password = $('#signUpPassword').value;
  if (!name || name.length > 80) return setNotice('Enter a name of 1–80 characters.', 'error');
  const button = $('#signUpSubmitBtn');
  button.disabled = true;
  button.textContent = 'Creating account…';
  setNotice('');
  try {
    const credential = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(credential.user, { displayName: name });
    await setDoc(doc(db, 'assignments', credential.user.uid), {
      displayName: name,
      sections: [{ title: 'Assignments', links: [] }],
      updatedAt: serverTimestamp(),
    });
    window.location.href = '/index.html?edit=1';
  } catch (error) {
    console.error('Account creation failed:', error);
    const fallback = error.code === 'permission-denied'
      ? 'Your account was created, but Firestore denied the profile save. Publish the provided firestore.rules and sign in again.'
      : explainAuthError(error);
    setNotice(fallback, 'error');
  } finally {
    button.disabled = false;
    button.textContent = 'Create account';
  }
});

$('#forgotPasswordBtn').addEventListener('click', async () => {
  if (!firebaseConfigured) return setNotice(firebaseSetupMessage(), 'error');
  const email = $('#signInEmail').value.trim();
  if (!email) return setNotice('Enter your email address first, then choose Forgot password.', 'error');
  try {
    await sendPasswordResetEmail(auth, email);
    setNotice('Password reset email sent. Check your inbox.', 'success');
  } catch (error) {
    setNotice(explainAuthError(error), 'error');
  }
});

if (!firebaseConfigured) {
  setupNotice.hidden = false;
  setupNotice.textContent = firebaseSetupMessage();
} else {
  onAuthStateChanged(auth, (user) => {
    if (user) {
      setNotice(`You are signed in as ${user.email}. Continue to the assignment board to edit your links.`, 'success');
      const continueBtn = document.createElement('a');
      continueBtn.className = 'button button-primary button-full continue-btn';
      continueBtn.href = '/index.html?edit=1';
      continueBtn.textContent = 'Continue to assignments';
      if (!$('.continue-btn')) notice.insertAdjacentElement('afterend', continueBtn);
    }
  });
}
