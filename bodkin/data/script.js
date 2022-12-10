window.addEventListener("load", function() {
  let selection = null;
  function handleClick(event) {
    if (selection) {
      const elems = document.querySelectorAll("." + selection);
      for (elem of elems) {
        elem.classList.remove("selected");
      }
      selection = null;
    }
    if (
      event.currentTarget.classList && event.currentTarget.classList.contains("ref")
    ) {
      for (const className of event.currentTarget.classList) {
        if (className.startsWith("group_")) {
          selection = className;
          const elems = document.querySelectorAll("." + className);
          for (elem of elems) {
            elem.classList.add("selected");
            // Move elem to end of svg to draw on top
            elem.parentElement.appendChild(elem);
          }
          break;
        }
      }
    }
    event.stopPropagation();

  }
  function handleEnter(event) {
    for (const className of event.target.classList) {
      if (className.startsWith("group_")) {
        const elems = document.querySelectorAll("." + className);
        for (elem of elems) {
          elem.classList.add("hover");
        }
        break;
      }
    }
  }
  function handleLeave(event) {
    for (const className of event.target.classList) {
      if (className.startsWith("group_")) {
        const elems = document.getElementsByClassName(className);
        for (elem of elems) {
          elem.classList.remove("hover");
        }
        break;
      }
    }
  }
  const refElems = document.getElementsByClassName("ref");
  window.addEventListener("click", handleClick);
  for (const elem of refElems) {
    elem.addEventListener("mouseenter", handleEnter);
    elem.addEventListener("mouseleave", handleLeave);
    elem.addEventListener("click", handleClick);
  }
});
