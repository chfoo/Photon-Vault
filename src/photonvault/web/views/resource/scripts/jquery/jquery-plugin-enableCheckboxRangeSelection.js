// jQuery checkbox utility plugin.
// By Henrik Nyh <http://henrik.nyh.se> 2009-04-27 under the MIT License.

(function($) {

  // Check a range of boxes by clicking one, then another while holding Shift or Command.
  // Code from http://www.barneyb.com/barneyblog/projects/jquery-checkbox-range-selection/
  // modified to support Command and so it can be reapplied after JS re-sort without issues.
  // $('#container :checkbox').enableCheckboxRangeSelection();
  $.fn.enableCheckboxRangeSelection = function() {
    var lastCheckbox = null;
    var $spec = this;
    $spec.unbind("click.checkboxrange");
    $spec.bind("click.checkboxrange", function(e) {
      if (lastCheckbox != null && (e.shiftKey || e.metaKey)) {
        $spec.slice(
          Math.min($spec.index(lastCheckbox), $spec.index(e.target)),
          Math.max($spec.index(lastCheckbox), $spec.index(e.target)) + 1
        ).attr("checked", e.target.checked);
      }
      lastCheckbox = e.target;
    });
    return $spec;
  };

  // $(':checkbox').checkAll();
  $.fn.checkAll = function() {
    return $(this).attr('checked', true);
  };
  
  // $(':checkbox').uncheckAll();
  $.fn.uncheckAll = function() {
    return $(this).attr('checked', false);
  }
  
  // Master checkbox that can check/uncheck other checkboxes:
  // $('#slaves :checkbox').checkAllWith('#master:checkbox');
  jQuery.fn.checkAllWith = function(master) {
    $slaves = $(this);
    $master = $(master);

    // If the control box is initially checked, check the others, but not the other way around.
    if ($master.attr('checked')) {
      $slaves.attr('checked', true);
    }

    (function($master, $slaves) { // Closure to allow multiple checkAllWith in one page
      $master.click(function() {
        $slaves.attr('checked', !!$master.attr('checked'));
      });
    })($master, $slaves);

    return $slaves;
  };

})(jQuery);