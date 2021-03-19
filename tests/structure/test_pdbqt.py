# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

import warnings
from tempfile import TemporaryFile
import glob
from os.path import join
import pytest
import numpy as np
import biotite.structure as struc
import biotite.structure.io.pdbqt as pdbqt
import biotite.structure.io.pdbx as pdbx
from ..util import data_dir


@pytest.mark.parametrize(
    "path", glob.glob(join(data_dir("structure"), "*.cif"))
)
def test_array_conversion(path):
    pdbx_file = pdbx.PDBxFile.read(path)
    ref_structure = pdbx.get_structure(
        pdbx_file, model=1, extra_fields=["charge"]
    )
    ref_structure.bonds = struc.connect_via_residue_names(ref_structure)

    pdbqt_file = pdbqt.PDBQTFile()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Ignore warnings about atoms not parametrized 
        mask = pdbqt.set_structure(pdbqt_file, ref_structure)
    ref_structure = ref_structure[mask]
    temp = TemporaryFile("r+")
    pdbqt_file.write(temp)

    temp.seek(0)
    pdbqt_file = pdbqt.PDBQTFile.read(temp)
    test_structure = pdbqt.get_structure(pdbqt_file, model=1)
    temp.close()

    assert np.allclose(test_structure.coord, ref_structure.coord)
    for category in test_structure.get_annotation_categories():
        if category == "element":
            # PDBQT uses special atom types, which replace the usual
            # elements
            # -> there cannot be equality of the 'element' annotation
            continue
        try:
            assert np.array_equal(
                test_structure.get_annotation(category),
                 ref_structure.get_annotation(category)
            )
        except AssertionError:
            print(f"Inequality in '{category}' category")
            raise
