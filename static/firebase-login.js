// firebase-login.js - Modified to work with Instagram-style login page
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyBMoMIJMqCIJZDgxEDpUShZCS2o1Ew_nxs",
    authDomain: "assignment---1-1e153.firebaseapp.com",
    projectId: "assignment---1-1e153",
    storageBucket: "assignment---1-1e153.appspot.com",
    messagingSenderId: "133737118405",
    appId: "1:133737118405:web:244db60467492f4f10ceac"
};

window.addEventListener("load", function() {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);
    console.log("Firebase App Initialized");
    
    // Check if we're on a login page
    const isLoginPage = window.location.pathname.includes('login');
    
    // Error handling functions
    function showLoginError(message) {
        const loginError = document.getElementById("login-error");
        if (loginError) {
            loginError.textContent = message;
            loginError.style.display = 'block';
        }
        
        const progressIndicator = document.getElementById("auth-progress");
        if (progressIndicator) {
            progressIndicator.style.display = 'none';
        }
        
        const loginBtn = document.getElementById("login-btn");
        if (loginBtn) {
            loginBtn.disabled = false;
        }
    }
    
    function showSignupError(message) {
        const signupError = document.getElementById("signup-error");
        if (signupError) {
            signupError.textContent = message;
            signupError.style.display = 'block';
        }
        
        const progressIndicator = document.getElementById("auth-progress");
        if (progressIndicator) {
            progressIndicator.style.display = 'none';
        }
        
        const signupBtn = document.getElementById("signup-btn");
        if (signupBtn) {
            signupBtn.disabled = false;
        }
    }
    
    document.getElementById("sign-up").addEventListener('click', function() {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        
        createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User Created:", user);
            
            // Get additional user data from localStorage if on login page
            if (isLoginPage) {
                const fullname = localStorage.getItem('pixelshare_fullname');
                const username = localStorage.getItem('pixelshare_username');
                
                // Here you could send this additional data to your backend
                console.log("Additional user data:", { fullname, username });
                
                // Clear the localStorage
                localStorage.removeItem('pixelshare_fullname');
                localStorage.removeItem('pixelshare_username');
            }
            
            user.getIdToken().then((token) => {
                document.cookie = `token=${token}; path=/; SameSite=Strict`;
                console.log("Signup Token Set:", document.cookie);
                window.location = "/";
            });
        })
        .catch((error) => {
            console.error("Signup Error:", error.code, error.message);
            
            // Show error message in UI if on login page
            if (isLoginPage) {
                let errorMessage = "Signup failed. Please try again.";
                
                if (error.code === 'auth/email-already-in-use') {
                    errorMessage = "Email already in use";
                } else if (error.code === 'auth/invalid-email') {
                    errorMessage = "Invalid email format";
                } else if (error.code === 'auth/weak-password') {
                    errorMessage = "Password is too weak";
                }
                
                showSignupError(errorMessage);
            }
        });
    });
    
    document.getElementById("login").addEventListener('click', function() {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        
        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            const user = userCredential.user;
            console.log("User Logged In:", user);
            user.getIdToken().then((token) => {
                document.cookie = `token=${token}; path=/; SameSite=Strict`;
                console.log("Login Token Set:", document.cookie);
                window.location = "/";
            });
        })
        .catch((error) => {
            console.error("Login Error:", error.code, error.message);
            
            // Show error message in UI if on login page
            if (isLoginPage) {
                let errorMessage = "Login failed. Please try again.";
                
                if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
                    errorMessage = "Invalid email or password";
                } else if (error.code === 'auth/invalid-email') {
                    errorMessage = "Invalid email format";
                } else if (error.code === 'auth/too-many-requests') {
                    errorMessage = "Too many failed login attempts. Please try again later";
                }
                
                showLoginError(errorMessage);
            }
        });
    });
    
    // Only initialize sign-out button if it exists
    const signOutBtn = document.getElementById("sign-out");
    if (signOutBtn) {
        signOutBtn.addEventListener('click', function() {
            signOut(auth)
            .then(() => {
                document.cookie = "token=; path=/; SameSite=Strict; expires=Thu, 01 Jan 1970 00:00:00 GMT"; 
                console.log("User Signed Out");
                window.location = "/";
            })
            .catch((error) => {
                console.error("Logout Error:", error.code, error.message);
            });
        });
    }
});

function updateUI(cookie) {
    const token = parseCookieToken(cookie);
    
    // Check if login-box exists before trying to hide it
    const loginBox = document.getElementById("login-box");
    const signOutBtn = document.getElementById("sign-out");
    
    if (loginBox && signOutBtn) {
        if (token.length > 0) {
            loginBox.hidden = true;
            signOutBtn.hidden = false;
        } else {
            loginBox.hidden = false;
            signOutBtn.hidden = true;
        }
    }
    
    // If on a non-login page and not authenticated, redirect to login
    const isLoginPage = window.location.pathname.includes('login');
    if (!isLoginPage && token.length === 0) {
        window.location.href = '/';
    }
    
    // If on login page and authenticated, redirect to home
    if (isLoginPage && token.length > 0) {
        window.location.href = '/';
    }
}

function parseCookieToken(cookie) {
    const strings = cookie.split(';');
    for (let i = 0; i < strings.length; i++) {
        const temp = strings[i].split('=');
        if (temp[0].trim() === "token") { 
            return temp[1];
        }
    }
    return "";
}