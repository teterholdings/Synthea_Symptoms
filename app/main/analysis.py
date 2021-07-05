import matplotlib
from matplotlib import pyplot as plt



def plot_int_counts(
    plot_dict: dict,
    relative = False,
    show = False,
    save = False,
    xlab = "Value",
    ylab = "Count",
    title = "",
    filename = "./count_plot.png",
    return_obj = False
) -> matplotlib.collections.PathCollection:
    """
    Plots counts from a dictionary with integer keys and
    integer values

    Args:
        plot_dict: (dict) object with integer keys and integer
            values (counts) to be plotted.
        show: (bool) if True will show the plot (default False).
        save: (bool) if True will save the plot (default False).
        xlab: (str) Label on x-axis (default "Value")
        ylab: (str) Label on y-axis (default "Count")
        title (str) Plot title (default "")
        filename: (str) Name of file to save plot to (default 
            "./count_plot.png").  Only used if save = True.
        return_obj: (bool) if True function returns the scatter 
            plot object.
    
    Returns:
        matplotlib.collections.PathCollection scatter plot object
    """
    try:
        assert all([isinstance(k,int) for k in plot_dict.keys()])
    except AssertionError as e:
        raise ValueError("plot_dict keys must be integral.")
    x = list(plot_dict.keys())
    if relative:
        y_raw = list(plot_dict.values())
        y_sum = sum(y_raw)
        y = [yr/y_sum for yr in y_raw]
        if ylab == "Count":
            ylab="Relative Frequency"
    else:
        y = list(plot_dict.values())
    s = plt.scatter(x,y)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.title(title)
    if show:
        plt.show()
    if save:
        plt.savefig(filename)
    if return_obj:
        return s
    else:
        plt.clf()
        plt.close()
        return None