(function () {
  var scriptSrc = document.currentScript && document.currentScript.src;
  var baseUrl = scriptSrc
    ? scriptSrc.replace(/\/embed\.js$/, "")
    : window.location.origin;

  var widgets = document.querySelectorAll("[data-widget]");

  for (var i = 0; i < widgets.length; i++) {
    var el = widgets[i];
    var widgetId = el.getAttribute("data-widget");
    if (!widgetId) continue;

    var iframe = document.createElement("iframe");
    iframe.src = baseUrl + "/embed/" + encodeURIComponent(widgetId);
    iframe.style.width = "100%";
    iframe.style.border = "none";
    iframe.style.overflow = "hidden";
    iframe.style.minHeight = "100px";
    iframe.setAttribute("loading", "lazy");
    iframe.setAttribute("title", "TrainerLab Widget " + widgetId);

    el.appendChild(iframe);
  }

  window.addEventListener("message", function (event) {
    if (!event.data || event.data.type !== "trainerlab-widget-resize") {
      return;
    }

    var iframes = document.querySelectorAll("iframe");
    for (var j = 0; j < iframes.length; j++) {
      if (iframes[j].contentWindow === event.source) {
        iframes[j].style.height = event.data.height + "px";
        break;
      }
    }
  });
})();
