/**
 *Toggle the class vis on the element provided with the ID id. Together with the css settings it can make an element collapse.
 *@param: id - the id of the Element whose class vis should be toggled
 */
function collapse(id) {
    var elem = document.getElementById(id);
    elem.classList.toggle("vis")
}

/**
 * Enables Bootstrap Tooltips
 */
 const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
 const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
 