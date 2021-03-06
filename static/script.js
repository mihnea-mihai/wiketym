// // https://www.w3schools.com/howto/howto_js_filter_dropdown.asp

// function filter(input) {
//     var filter, ul, li, a, i;
//     filter = input.value.toUpperCase();
//     div = input.parentElement;
//     a = div.getElementsByTagName("a");
//     for (i = 0; i < a.length; i++) {
//         txtValue = a[i].textContent || a[i].innerText;
//         if (txtValue.toUpperCase().indexOf(filter) > -1) {
//             a[i].style.display = "";
//         } else {
//             a[i].style.display = "none";
//         }
//     }
// }

// function setValue(option) {
//     text = option.textContent || option.innerText;
//     parent = option.parentElement.parentElement
//     input = parent.getElementsByTagName("input")[0]
//     input.value = text
//     filter(input)
//     hideDropdown(option)
// }

// function showDropdown(input) {
//     filter(input)
//     parent = input.parentElement
//     options = parent.getElementsByTagName("div")[0]
//     options.style.display = ""
//     options.style.height = "20vh"
// }

// function hideDropdown(option) {
//     option.parentElement.style.display = "none"
// }

function addWord() {
    words = document.getElementById('words');
    wordList = words.children;

    index = wordList.length;
    newWord = wordList[0].cloneNode(true);

    lemma = newWord.querySelector('.lemma');
    lemma.querySelector('label')
        .setAttribute('for', 'lemma' + String(index));
    lemmaInput = lemma.querySelector('input')
    lemmaInput.setAttribute('name', 'lemma' + String(index));
    lemmaInput.value = ''

    language = newWord.querySelector('.language');
    language.querySelector('label')
        .setAttribute('for', 'lang_code' + String(index));
    language.querySelector('select')
        .setAttribute('name', 'lang_code' + String(index));

    words.insertBefore(newWord, document.getElementById('word-buttons'));
    document.getElementById('del-word').removeAttribute('disabled')
}

function removeWord() {
    words = document.getElementsByClassName('word')
    wordDiv = document.getElementById('words')
    wordDiv.removeChild(words[words.length - 1])
    if (words.length <= 1) {
        document.getElementById('del-word').setAttribute('disabled', true)
    }
}

function togglePreview() {
    body = document.getElementsByTagName('body')[0]
    form = document.getElementsByTagName('form')[0]
    if (document.getElementById('preview').checked) {
        body.className = 'split'
        form.setAttribute('target', 'preview-iframe')
    }
    else {
        body.className = 'single'
        form.setAttribute('target', '_blank')
    }
}
