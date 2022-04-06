import os

# import numpy as np
import pandas as pd
# from vmtk import pypes
# from vmtk import vmtkscripts
import vmtk_sss_lts_rts as vslr


def runner(subject_list, vessel_type, vessel_list):

    base_dir = os.path.abspath('../../../../')
    output_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                              'vmtk_artery_vein_2')
    segmentation_dir = os.path.join(base_dir, 'derivatives', 'manualwork',
                                    'segmentations', 'artery_vein')
    df_list = []
    # diameter_df_list = []
    for subject in subject_list:

        for vessel in vessel_list:
            print('==== Starting: ' + vessel + ' ====')
            input_fn_pattern = 'sub-' + subject + '_' + vessel_type
            output_fn_pattern = ('sub-' + subject + '_' + vessel_type + '_' +
                                 vessel)
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
    pass


def main():
    subject_list = ['02']
    # vessel_list = ['artery', 'vein']
    vessel_list = [
        'left_vert_artery', 'right_vearteryrt_artery', 'basilar_artery'
    ]
    vessel_list = ['LA', 'LB', 'LC', 'LD', 'LE']
    vessel_type = 'artery'
    # runner(subject_list, vessel_type, vessel_list)
    # vessel_list = ['LTS', 'SSS', 'RTS']
    # vessel_type = 'vein'
    runner(subject_list, vessel_type, vessel_list)
    vessel_list = ['RA', 'RB', 'RC', 'RD', 'RE']
    runner(subject_list, vessel_type, vessel_list)
    pass


if __name__ == "__main__":
    main()