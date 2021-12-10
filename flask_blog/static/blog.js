var postContents = {}


const updatePost = (postid) =>{
    let post = document.getElementById(postid)
    let para = post.children[0]
    let content = para.innerText
    postContents[postid] = content
    para.remove()
    
    let inputHTML = `<input id="${postid}-input" form="create-post" type="text" name="new-content">`
    post.insertAdjacentHTML('afterbegin', inputHTML)
    let [input, div] = Array.from(post.children)
    
    input.value = content
    input.style.width = "99%"
    input.style.marginLeft = "0"
    input.style.marginRight = "0"
    input.style.marginTop = "10px"
    input.style.marginBottom = "10px"
    input.style.textAlign = "left"

    let [_, okBtn, delBtn] = Array.from(div.children)
    okBtn.innerText = "OK"
    okBtn.removeAttribute("onClick")
    
    delBtn.innerText = "Cancel"
    delBtn.removeAttribute("formaction")
    delBtn.removeAttribute("type")
    delBtn.removeAttribute("form")
    delBtn.setAttribute('onClick', `cancelUpdate('${postid}')`)

    window.setTimeout(() => {
        okBtn.setAttribute("onClick", `commitUpdate('${postid}')`)
    }, 1000)
}


const cancelUpdate = (postid) => {
    let post = document.getElementById(postid)
    let input = post.children[0]
    let content = postContents[postid]
    input.remove()
    
    let paraHTML = '<p class="blog-post-content"></p>'
    post.insertAdjacentHTML('afterbegin', paraHTML)
    let [para, div] = Array.from(post.children)
    para.innerText = content

    let [_, updateBtn, delBtn] = Array.from(div.children)
    updateBtn.innerText = "Edit"
    updateBtn.removeAttribute("formaction")
    updateBtn.removeAttribute("type")
    updateBtn.removeAttribute("form")
    updateBtn.setAttribute("onClick", `updatePost(${postid})`)
    
    delBtn.innerText = "Delete"
    delBtn.removeAttribute('onClick')
    
    window.setTimeout(() => {
        delBtn.setAttribute("formaction", `/delete/${postid}`)
        delBtn.setAttribute("type", "submit")
        delBtn.setAttribute("form", "create-post")
    }, 1000)
}


const commitUpdate = (postid) => {
    let form = document.getElementById("create-post")
    form.setAttribute("action", `/update/${postid}`)
    form.submit()
    form.setAttribute("action", "/create")
}
