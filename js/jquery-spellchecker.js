var _gaq = _gaq || [];
      _gaq.push(['_setAccount', 'UA-1636725-34']);
      _gaq.push(['_trackPageview']);
      (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();

(function(){

      var spellchecker = new $.SpellChecker('#html-demo-content', {
        lang: 'en',
        parser: 'html',
        webservice: {
          path: '../webservices/php/SpellChecker.php',
          driver: 'PSpell'
        },
        suggestBox: {
          position: 'below',
          offset: 1
        }
      });

      // Bind spellchecker handler functions
      spellchecker.on('check.success', function() {
        alert('There are no incorrectly spelt words!');
      });

      // Check the spelling when user clicks on button
      $("#check-spelling-html").click(function(e){
        spellchecker.check();
      });
    })();
