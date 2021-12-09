var userData = {}

const saveUserId = (userid) => {
    userData["id"] = parseInt(userid)
    console.log(userData["id"])
}

const editUsername = () => {
    let btn = document.getElementById("usernameBtn")
    let usernameField = document.getElementById("username")
    let username = usernameField.value
    userData["username"] = username

    let html = "<button id=\"commitUsernameBtn\" onClick=\"changeUsername()\">Commit changes</button>"
    btn.insertAdjacentHTML("afterend", html)

    usernameField.removeAttribute("disabled")
    btn.setAttribute("onClick", "cancelEditUsername()")
    btn.innerText = "Cancel"
}

const changeUsername = () => {
    let userid = userData["id"]
    let url = `/admin/users/${userid}/edit/username`
    let form = document.getElementById("manage-user")

    form.setAttribute("action", url)
    form.submit()
}

const cancelEditUsername = () => {
    let element = document.getElementById("commitUsernameBtn")
    element.parentElement.removeChild(element)

    let btn = document.getElementById("usernameBtn")
    btn.setAttribute("onClick", "editUsername()")
    let usernameField = document.getElementById("username")
    
    usernameField.value = userData["username"]
    usernameField.setAttribute("disabled", true)
    btn.innerText = "Edit"
}

const editEmail = () => {
    let btn = document.getElementById("emailBtn")
    let emailField = document.getElementById("email")
    let email = emailField.value
    userData["email"] = email

    let html = "<button id=\"commitEmailBtn\" onClick=\"changeEmail()\">Commit changes</button>"
    btn.insertAdjacentHTML("afterend", html)

    emailField.removeAttribute("disabled")
    btn.setAttribute("onClick", "cancelEditEmail()")
    btn.innerText = "Cancel"
}

const changeEmail = () => {
    let userid = userData["id"]
    let url = `/admin/users/${userid}/edit/email`
    let form = document.getElementById("manage-user")

    form.setAttribute("action", url)
    form.submit()
}

const cancelEditEmail = () => {
    let element = document.getElementById("commitEmailBtn")
    element.parentElement.removeChild(element)

    let btn = document.getElementById("emailBtn")
    btn.setAttribute("onClick", "editEmail()")
    let emailField = document.getElementById("email")
    
    emailField.value = userData["email"]
    emailField.setAttribute("disabled", true)
    btn.innerText = "Edit"
}