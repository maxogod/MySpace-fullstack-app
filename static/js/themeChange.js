
const blueInverse = '#8e3922'

const lightTheme = {
    '--color-main': '#71d0dd',
    '--color-main-light': '#000000',
    '--color-dark': '#ffffff',
    '--color-dark-medium': '#f1f1f1',
    '--color-dark-light': '#b2b2b2',
    '--color-light': '#000000',
    '--color-gray': '#7b7b7b',
    '--color-light-gray': '#000000',
    '--color-bg': '#f2f2f5',
    '--color-success': '#5dd693',
    '--color-error': '#fc4b0b',
}

let settings = JSON.parse(localStorage.getItem('settings'))

if (settings && settings.theme === 'light') {
    for (let [key, value] of Object.entries(lightTheme)) {
        document.querySelector(':root').style.setProperty(key, value)
    }
} else if (settings && settings.theme === 'dark') {
    document.getElementById('logo').style.setProperty('filter', 'invert(1)')
} else if (!settings) {
    let newSettings = { theme: 'dark' }
    localStorage.setItem('settings', JSON.stringify(newSettings));
}


document.getElementById('changeThemes').onclick = function () {
    let settings = JSON.parse(localStorage.getItem('settings'))
    let newSettings = {};
    if (settings.theme === 'dark') {
        newSettings.theme = 'light'
    } else {
        newSettings.theme = 'dark'
    }
    localStorage.setItem('settings', JSON.stringify(newSettings));
}
