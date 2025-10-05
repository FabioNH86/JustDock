import cz.siret.prank.program.params.Params

(params as Params).with {

    /**
     * produce pymol visualisations
     */
    visualizations = false

    /**
     * copy all protein pdb files to visualization folder (making visualizations portable)
     */
    vis_copy_proteins = false

	/**
     * output detailed tables for all proteins, ligands and pockets or residues
     */
    log_cases = false

	/**
     * print log messages to file (run.log in outdir)
     */
    log_to_file = false

}
