# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 13:47:36 2014

@author: christophe
"""

import math
import matplotlib.pylab as plt


def plot_lines(df, x_col, y_col, colorby_col=None, splitby_col=None,
               color_map=None, use_suptitle=True, use_subplots=False):
    """Plot a metric of mapreduce as a function of parameters.
    Data are first grouped by split_by to produce one figure per value.
    In each figure, data are grouped by colorby_col to create one line per
    value.
    If you have other parameters you must first group the results according to
    this parameter and then pass them to this function.
    We don't allow a lot of plot options but they can be changed with
    matplotlib API. The only option is the colormap (because line plot don't
    use it so we emulate that functionality).
    However we try to be a bit smart on axis labels.

    Parameters
    ----------
    df: the dataframe containing the results.

    x_col: column name (or index level) of the x-axis.

    y_col: column name of the y-axis (it makes no sense to have an index level
    here).

    colorby_col: column name (or index level) that define colored lines.
    One line per value or level.

    splitby_col: column name (or index level) that define how to split figures.
    One figure per value or level (see use_subplots).

    color_map: color map to use (if None, use default colors). It's a
    dictionary whose key are the values of colorby_col and the values a
    matplotlib color.

    use_suptitle: if True, use values of splitby_col as suptitle (it's hard to
    tune).

    use_subplots: create a subplot instead of a figure for each value of
    splitby_col

    Returns
    -------
    handles: dictionnary of figure handles.
    The key is the value of splitby_col and the value is the figure handler (or
    the subplot if use_subplots is True).
    """
    # pandas.DataFrame.plot don't work properly if x_col is an index
    import pandas.core.common as com
    x_col_is_index = com.is_integer(x_col)
    # x_name is the name of the column/index used for x axis
    x_name = df.index.names[x_col] if x_col_is_index \
                                   else x_col
    colorby_col_is_index = com.is_integer(colorby_col)
    # colorby_name is the name of the column/index used for lines
    colorby_name = df.index.names[colorby_col] if colorby_col_is_index \
                                               else colorby_col
    # Not useful for now
    splitby_col_is_index = com.is_integer(splitby_col)

    # Labels (note that y_col is supposed to be a good label here)
    x_label = x_name
    colorby_label = colorby_name

    try:
        # Try to group by column name
        fig_groups = df.groupby(splitby_col)
    except KeyError:
        try:
            # Try to group by index level
            fig_groups = df.groupby(level=splitby_col)
        except:
            raise Exception("Cannot group by splitby_col.")
    handles = {}
    fig_created = False
    for i, (splitby_col_val, splitby_col_group) in enumerate(fig_groups, 1):
        if use_subplots:
            if not fig_created:
                h = plt.figure()
                n_plots = len(fig_groups)
                n_rows = math.floor(math.sqrt(n_plots))
                n_cols = math.ceil(float(n_plots) / float(n_rows))
                fig_created = True
            handles[splitby_col_val] = plt.subplot(n_rows, n_cols, i)
        else:
            h = plt.figure()
            handles[splitby_col_val] = h
        if use_suptitle:
            plt.suptitle(splitby_col_val)
        try:
            # Try to group by column name
            color_groups = splitby_col_group.groupby(colorby_col)
        except KeyError:
            try:
                # Try to group by index level
                color_groups = splitby_col_group.groupby(level=colorby_col)
            except:
                raise Exception("Cannot group by colorby_col.")
        for colorby_col_val, colorby_col_group in color_groups:
            if x_col_is_index:
                # Remove index: x_col is now referred as x_name
                colorby_col_group.reset_index(level=x_col, inplace=True)
            colorby_col_group.sort(x_name, inplace=True)
            if color_map is None:
                colorby_col_group.plot(x=x_name, y=y_col,
                                       label=colorby_col_val)
            else:
                colorby_col_group.plot(x=x_name, y=y_col,
                                       label=colorby_col_val,
                                       color=color_map[colorby_col_val])
            plt.xlabel(x_label)
            plt.ylabel(y_col)
        plt.legend(title=colorby_label)
    return handles
