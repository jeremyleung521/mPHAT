"""
Discretize your MD trajectories (or WE simulations) into states.
"""
import logging
import numpy
from mphat.extloader import *
from mphat.io import expanded_load, output_file

log = logging.getLogger(__name__)


def assign(input_array):
    """
    This is an example function for mapping a list of features to state IDs. This should be subclassed.

    Parameters
    ----------
    input_array : numpy.ndarray or list
        An array generated from expanded_load.

    Returns
    -------
    state_list : list
        A list containing
    """
    state_list = []
    for val in input_array:
        if val[0] >= -180 and val[0] <= -45 and val[1] >= -55 and val[1] <= 30:  # Phi/Psi for Alpha Helix
            state_list.append(0)
        elif val[0] >= 165 and val[0] <= 180 and val[1] >= -55 and val[1] <= 30:
            state_list.append(0)
        elif val[0] >= -170 and val[0] <= -55 and val[1] >= 40 and val[1] <= 100:  # Phi/Psi for C7eq
            state_list.append(1)
        elif val[0] >= 25 and val[0] <= 90 and val[1] >= -55 and val[1] <= 0:  # Phi/Psi for C7ax
            state_list.append(2)
        else:
            state_list.append(3)

    return state_list


def main(arguments):
    """
    Main function that executes the whole ``match`` step. Also called by the
    ``entry_point()`` function.

    If it's an HDF5 file, it'll just run ``w_assign`` (as w_assign).

    Parameters
    ----------
    arguments : argparse.Namespace
        A Namespace object will all the necessary parameters.

    """
    if arguments.we:
        try:
            import westpa
            from westpa.cli.tools import w_assign
        except ModuleNotFoundError as e:
            print(e)
            raise ModuleNotFoundError("Trying to discretize an HDF5 file but can't import w_assign")

        if arguments.we and arguments.input_name != arguments.west_name:
            setattr(arguments, 'west_name', arguments.input_name)
            log.debug("Replacing parameter `west_name` with `input_name`")

        if arguments.we and arguments.output_name != arguments.output:
            setattr(arguments, 'output_name', arguments.output_name)
            log.debug("Replacing parameter `output_name` with `assign_name`")

        if arguments.we and arguments.rcfile != arguments.assign_args.rcfile:
            setattr(arguments, 'rcfile', arguments.assign_args.rcfile)
            log.debug("Replacing parameter `rcfile` with `assign_args.rcfile`")

        # This basically some logic that's wrapped up in WESTTool.main() for convenience.
        # It needs to be explicitly called like this because the args are captured and set in make_parser_and_process()
        #   which we don't want to call, because we don't want to make a parser.
        #   We just want to process the args that "would've" been captured if called from CLI.

        tool = w_assign.WAssign()

        # Prepare and instantiate work manager
        tool.wm_env.process_wm_args(arguments.assign_args)
        tool.work_manager = tool.wm_env.make_work_manager()

        tool.process_all_args(arguments.assign_args)
        with tool.work_manager:
            if tool.work_manager.is_master:
                tool.go()
            else:
                tool.work_manager.run()
    else:
        input_array = expanded_load(arguments.input_name, arguments.stride)

        # Replacing assign_func with what's given
        if arguments.assign_func != 'default_assign':
            import sys
            import os
            sys.path.append(os.getcwd())

            assign = get_object(arguments.assign_func)
            log.warning(f'WARNING: Replaced assign() with {arguments.assign_func}')

        out_array = assign(input_array)
        output_file(out_array, arguments.output_file)


if __name__ == "__main__":
    """
    For calling `discretize.py` directly. Note all of the parameters are specified manually here.
    """
    import argparse

    args = argparse.Namespace(
        we=True,  # Analyzing a WE simulation
        input_name='dihedral.npy',  # Input data for state assignment. Something like 'dihedral.npy'.
        output_name='discretized.npy',  # Output file name for the state assignment.
        assign_func='assign_func',  # Assign function that dictates how to assign states
        west_name='west.h5',  # Name of input HDF5 file (e.g., west.h5)
        assign_name='ANALYSIS/TEST/assign.h5',  # Name of output assign.h5 file
        rcfile='west.cfg', # west.cfg file
        assign_args=argparse.Namespace(  # These are arguments for w_assign
            verbosity='verbose',  # Verbose or debug
            rcfile='west.cfg',  # west.cfg
            max_queue_length=None,
            we_h5filename='west.h5',  # west.h5 path
            construct_dataset=None,  # If you need some custom auxiliary dataset
            dsspecs=None,
            output='assign.h5',  # Output file
            subsample=None,
            config_from_file=True,  # Read config from rcfile
            scheme='TEST',  # Scheme name
        ),
    )
    main(args)
