function urlify(selector) {
  if (!Array.isArray(selector)) selector = [selector];

  selector.forEach(s => {
    var targets = document.querySelectorAll(s);
    if (!targets) return;
    for (let target of targets) {
      const LNumberRegex = /L\d{4}:\d+/g;
      const FPIdentifierRegex = /FP-(\w|\d)+/g;
      target.innerHTML = target.innerHTML
        .replace(LNumberRegex, function(LNumber) {
          return '<a href="https://fornpunkt.se/apis/kmr-identification-resolver/v1/' + LNumber + '">' + LNumber + '</a>';
        })
        .replace(FPIdentifierRegex, function(FPIdentifier) {
          return '<a href="https://fornpunkt.se/lamning/' + FPIdentifier.replace('FP-', '') + '">' + FPIdentifier + '</a>';
        });
    } 
  });
}

urlify(['p']);
