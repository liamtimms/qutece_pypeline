import os

import numpy as np
import pandas as pd
import vmtk_sss_lts_rts as vslr
from vmtk import pypes, vmtkscripts


def runner(subject_list, vessel_type, vessel_list):
    base_dir = os.path.abspath('../')
    output_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                              'vmtk_thrombus')
    segmentation_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                                    'segmentations', 'thrombus')
    df_list = []
    diameter_df_list = []
    for subject in subject_list:

        for vessel in vessel_list:
            input_fn_pattern = 'rsub-' + subject + '_' + vessel_type
            output_fn_pattern = 'sub-' + subject + '_' + vessel_type + '_' + vessel
            centerline_vtp = os.path.join(
                output_dir, output_fn_pattern + '_centerlines.vtp')
            if not os.path.exists(centerline_vtp):
                centerline_vtp = vslr.vmtk_processor(input_fn_pattern, vessel,
                                                     subject, output_dir,
                                                     segmentation_dir)
            centerline_df = vslr.centerline_extractor(centerline_vtp)
            centerline_df['vessel'] = vessel
            centerline_df['subject'] = subject
            df_list.append(centerline_df)

    Centerline_SUMMARY = pd.concat(df_list)
    Centerline_SUMMARY['vessel_type'] = vessel_type

    Diameter_SUMMARY = Centerline_SUMMARY.copy()
    Diameter_SUMMARY.set_index(['subject', 'vessel'], inplace=True)
    Diameter_SUMMARY_csv = os.path.join(
        output_dir, f"SUMMARY-diameter_of_{vessel_type}.csv")
    Diameter_SUMMARY.to_csv(Diameter_SUMMARY_csv)
    Diameter_SUMMARY['diameter'].groupby(level=[0, 1]).agg(['mean', 'std'])
    Diameter_SUMMARY['distance'].groupby(level=[0, 1]).agg(['max'])

    return Diameter_SUMMARY

def centerline_load(file_name):
    # centerline reading
    centerlineReader = vmtkscripts.vmtkSurfaceReader()
    centerlineReader.InputFileName = file_name
    centerlineReader.Execute()
    clNumpyAdaptor = vmtkscripts.vmtkCenterlinesToNumpy()
    clNumpyAdaptor.Centerlines = centerlineReader.Surface
    clNumpyAdaptor.Execute()
    numpyCenterlines = clNumpyAdaptor.ArrayDict

    points = numpyCenterlines['Points']
    pointsIds = np.arange(len(points))
    radius = numpyCenterlines['PointData']['MaximumInscribedSphereRadius']
    segPointIds = numpyCenterlines['CellData']['CellPointIds']
    numSegments = len(segPointIds)
    return

def main():
    subject_list = ['03']
    # vessel_list = ['artery', 'vein']
    # vessel_list = ['left_vert_artery', 'right_vearteryrt_artery', 'basilar_artery']
    # vessel_type = 'artery'
    # runner(subject_list, vessel_type, vessel_list)
    # vessel_list = ['SSS', 'S1', 'S2', 'S3']
    vessel_list = ['SSS']
    vessel_type = 'vein'
    runner(subject_list, vessel_type, vessel_list)
    # vessel_list = ['thrombus']
    # vessel_type = 'thrombus'
    # runner(subject_list, vessel_type, vessel_list)
    pass


if __name__ == "__main__":
    main()
