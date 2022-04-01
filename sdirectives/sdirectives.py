import os
import glob
from pathlib import Path
from datetime import datetime

import numpy as np

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import properties
from SimPEG.directives import InversionDirective


class PlotAndSaveEveryIteration(InversionDirective):
    """Saves inversion parameters and plots at every iteration."""

    # Custom directive
    1
    # TODO: Restarting possibility
    #
    # - One Plot combining misfit and Tikhonov curves
    # - logging!
    # - load/get data

    path = properties.String("directory to save results in", default="./data")
    remove = properties.Bool("remove existing files", default=False)
    name = properties.String(
        "root of the filename to be saved", default="InversionModel"
    )

    def initialize(self):
        print(f"Files and plots are saved as '{self.full_path}*'.")
        if os.path.isfile(self.full_path+'.npz'):
            if self.remove:
                print(f"Removing existing files '{self.full_path}*'.")
                for p in Path(self.path).glob(f'{self.file_name}.*'):
                    p.unlink()
                for p in Path(self.path).glob(f'{self.file_name}-???.npz'):
                    p.unlink()
            else:
                msg = "Inversion exists; set `overwrite=True` to overwrite."
                raise FileExistsError(msg)

        self.beta = []
        self.phi = []
        self.phi_d = []
        self.phi_m = []
        self.target_misfit = self.invProb.dmisfit.simulation.survey.nD / 2.0

    def __repr__(self):
        return (
            "SimPEG-directive for SimPEG(emg3d). Files & plots are saved in\n"
            f"{self.full_path}*"
        )

    def endIter(self):

        self.beta.append(self.invProb.beta)
        self.phi.append(self.opt.f)
        self.phi_d.append(self.invProb.phi_d)
        self.phi_m.append(self.invProb.phi_m)
        self.it = self.opt.iter

        # Update overall values.
        np.savez_compressed(
            self.full_path,
            it=self.it,
            beta=self.beta,
            phi=self.phi,
            phi_d=self.phi_d,
            phi_m=self.phi_m,
            target_misfit=self.target_misfit
        )

        # Save data of this iteration.
        np.savez_compressed(
            self.full_path+f"-{self.opt.iter:03d}",
            it=self.opt.iter,
            beta=self.invProb.beta,
            phi_d=self.invProb.phi_d,
            phi_m=self.invProb.phi_m,
            f=self.opt.f,
            m=self.invProb.model,
            dpred=self.invProb.dpred,
        )

        # Save curve.
        self.plot_curves(fname=f"{self.full_path}.png")

    def load_results(self, file_name, it=None, path='data', verb=0):
        # Loads last iteration if it=None.
        self.path = path
        self._file_name = file_name
        self._full_path = None
        full_path = self.full_path

        if it is None:
            ff = glob.glob(full_path+"-???.npz")
            if len(ff) == 0:
                raise FileNotFoundError(f"No such files: '{full_path}-???.npz'")
            self.it = np.max([int(f.split(".")[-2].split("-")[-1]) for f in ff])
        else:
            self.it = int(it)

        iteration_file = full_path+f"-{int(self.it):03d}.npz"
        with np.load(iteration_file) as data:
            self.f = data['f']
            self.m = data['m']
            self.dpred = data['dpred']

        with np.load(full_path+".npz") as data:
            self.beta = data["beta"][:self.it]
            self.phi = data["phi"][:self.it]
            self.phi_d = data["phi_d"][:self.it]
            self.phi_m = data["phi_m"][:self.it]
            self.target_misfit = data["target_misfit"]

        if verb > 0:
            print(f"Loaded {iteration_file}")

    @classmethod
    def from_file(cls, file_name, it=None, path='data', verb=0):
        save = cls(path=path)
        save.load_results(file_name, it, path, verb)
        return save

    @property
    def file_name(self):
        # Create file name for this inversion run.
        if getattr(self, "_file_name", None) is None:
            date = datetime.now().strftime("%Y-%m-%d_%H-%M")
            if self.name == 'InversionModel':
                self._file_name = f"{date}"
            else:
                if 'datetime' in self.name:
                    self.name = self.name.replace('datetime', f'{date}')
                self._file_name = self.name
        return self._file_name

    @property
    def full_path(self):
        # Create full path for this inversion run.
        if getattr(self, "_full_path", None) is None:
            # Get absolute path and ensure it exists.
            abspath = os.path.abspath(self.path)
            if not os.path.isdir(abspath):
                os.mkdir(abspath)
            self._full_path = os.path.join(abspath, self.file_name)
            self.path = abspath

        return self._full_path

    def plot_curves(self, fname):

        plt.style.use('bmh')

        self.i_target = np.where(self.phi_d < self.target_misfit)[0]
        self.i_target = None if self.i_target.size == 0 else self.i_target[0]

        fig, axs = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
        ((ax1, ax3), (ax2, ax4)) = axs

        ax1.loglog(self.beta, self.phi_d, "k.-")
        ax1.set_xlabel("$\\beta$", fontsize=14)
        ax1.set_ylabel("$\phi_d$", fontsize=14)
        ax1.invert_xaxis()

        ax2.loglog(self.beta, self.phi_m, "k.-")
        ax2.set_xlabel("$\\beta$", fontsize=14)
        ax2.set_ylabel("$\phi_m$", fontsize=14)
        ax2.invert_xaxis()

        ax3.plot(self.phi_m, self.phi_d, "k.-")
        ax3.set_xlabel("$\phi_m$", fontsize=14)
        ax3.set_ylabel("$\phi_d$", fontsize=14)

        if self.i_target is not None:
            ax1.plot(self.beta[self.i_target], self.phi_d[self.i_target],
                     "k*", ms=10)
            ax2.plot(self.beta[self.i_target], self.phi_m[self.i_target],
                     "k*", ms=10)
            ax3.plot(self.phi_m[self.i_target], self.phi_d[self.i_target],
                     "k*", ms=10)

        ax4b = ax4.twinx()
        ax4.semilogy(np.arange(self.it)+1, self.phi_d, "k", label="$\phi_d$")
        ax4b.semilogy(np.arange(self.it)+1, self.phi_m, "C0", label="$\phi_m$")
        ax4.legend(loc=6)
        ax4b.legend(loc=7)

        ax4.axhline(self.target_misfit, c="k", ls=":")

        ax4.set_xlabel("Iteration")
        ax4.set_ylabel("$\phi_d$")
        ax4b.set_ylabel("$\phi_m$", color="C0")
        ax4b.tick_params(axis="y", which="both", colors="C0")

        fig.savefig(fname, bbox_inches='tight', dpi=300, facecolor='w')
        plt.close(fig)
